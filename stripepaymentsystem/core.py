import os
import stripe
import datetime
from typing import Optional, Dict, List, Union
import discord
from discord import ui
from discord.utils import escape_markdown

class StripeCore:
    """Handles Stripe operations, UI components, and webhooks."""
    
    def __init__(self, bot, db_partition):
        self.bot = bot
        self.db = db_partition
        self.stripe = None
        self.mode = "test"  # Default to test mode
        
        # Initialize Stripe if API key exists
        if "STRIPE_API_KEY" in os.environ:
            self._init_stripe(os.environ["STRIPE_API_KEY"])
    
    def _init_stripe(self, api_key: str) -> bool:
        """Initialize Stripe client and verify connection."""
        try:
            self.stripe = stripe.Stripe(api_key)
            self.stripe.Account.retrieve()  # Test connection
            return True
        except stripe.error.StripeError as e:
            self.bot.log.error(f"Stripe init failed: {e}")
            return False
    
    # --------------------------------------------------
    # Stripe Operations
    # --------------------------------------------------
    
    async def create_payment_link(
        self,
        amount: float,
        currency: str,
        product_name: str,
        description: str = "",
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """Generate a Stripe payment link with QR code."""
        if not self.stripe:
            return None
            
        try:
            session = self.stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {
                            "name": product_name,
                            "description": description[:200],
                        },
                        "unit_amount": int(amount * 100),  # Convert to cents
                    },
                    "quantity": 1,
                }],
                mode="payment",
                metadata=metadata or {},
                success_url="https://example.com/success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url="https://example.com/cancel",
            )
            return session.url
        except stripe.error.StripeError as e:
            self.bot.log.error(f"Payment link creation failed: {e}")
            return None
    
    async def validate_payment(self, payment_intent_id: str) -> Dict:
        """Check payment status via Stripe API."""
        try:
            intent = self.stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                "status": intent.status,
                "amount": intent.amount / 100,
                "currency": intent.currency.upper(),
                "card_type": intent.charges.data[0].payment_method_details.card.brand,
                "receipt_url": intent.charges.data[0].receipt_url
            }
        except stripe.error.StripeError as e:
            self.bot.log.error(f"Payment validation failed: {e}")
            return {"status": "error", "details": str(e)}
    
    # --------------------------------------------------
    # UI Components
    # --------------------------------------------------
    
    def embed_payment_request(
        self,
        amount: float,
        currency: str,
        product: str,
        description: str = "",
        recipient: Optional[discord.User] = None
    ) -> discord.Embed:
        """Embed for mods to review before sending payment request."""
        embed = discord.Embed(
            title="💳 Payment Request",
            color=0x6772FF  # Stripe purple
        )
        embed.add_field(name="Product", value=escape_markdown(product), inline=True)
        embed.add_field(name="Amount", value=f"{amount:.2f} {currency.upper()}", inline=True)
        if description:
            embed.add_field(name="Description", value=escape_markdown(description), inline=False)
        if recipient:
            embed.set_footer(text=f"Recipient: {recipient.display_name} ({recipient.id})")
        return embed
    
    def embed_payment_success(
        self,
        amount: float,
        currency: str,
        product: str,
        receipt_url: Optional[str] = None
    ) -> discord.Embed:
        """Embed shown to users after successful payment."""
        embed = discord.Embed(
            title="✅ Payment Successful",
            description=f"Thank you for your purchase of **{escape_markdown(product)}**",
            color=0x00C853  # Green
        )
        embed.add_field(name="Amount Paid", value=f"{amount:.2f} {currency.upper()}")
        if receipt_url:
            embed.add_field(name="Receipt", value=f"[View Receipt]({receipt_url})", inline=False)
        return embed
    
    def embed_payment_details(
        self,
        payment_data: Dict,
        user: Optional[discord.User] = None
    ) -> discord.Embed:
        """Detailed payment info for mods."""
        embed = discord.Embed(
            title="Payment Details",
            color=0x2196F3  # Blue
        )
        if user:
            embed.set_author(name=f"{user.display_name}", icon_url=user.display_avatar.url)
        
        embed.add_field(name="Status", value=payment_data.get("status", "unknown").title(), inline=True)
        embed.add_field(name="Amount", value=f"{payment_data.get('amount', 0):.2f} {payment_data.get('currency', 'USD')}", inline=True)
        embed.add_field(name="Card Type", value=payment_data.get("card_type", "Unknown").title(), inline=True)
        
        if "timestamp" in payment_data:
            embed.timestamp = datetime.datetime.fromisoformat(payment_data["timestamp"])
        
        if "stripe_id" in payment_data:
            embed.set_footer(text=f"Stripe ID: {payment_data['stripe_id']}")
        
        return embed
    
    class ModeSelectView(ui.View):
        """View for selecting test/live mode."""
        def __init__(self, callback):
            super().__init__(timeout=300)
            self.callback = callback
        
        @ui.button(label="Test Mode", style=discord.ButtonStyle.grey, emoji="🧪")
        async def test_mode(self, interaction: discord.Interaction, button: ui.Button):
            await self.callback(interaction, "test")
        
        @ui.button(label="Live Mode", style=discord.ButtonStyle.red, emoji="⚠️")
        async def live_mode(self, interaction: discord.Interaction, button: ui.Button):
            await self.callback(interaction, "live")
    
    # --------------------------------------------------
    # Webhook Handler
    # --------------------------------------------------
    
    async def handle_webhook_event(self, payload: Dict) -> Optional[Dict]:
        """Process Stripe webhook events."""
        event = payload.get("type")
        data = payload.get("data", {}).get("object", {})
        
        if event == "payment_intent.succeeded":
            return await self._handle_payment_success(data)
        elif event == "payment_intent.payment_failed":
            return await self._handle_payment_failure(data)
        return None
    
    async def _handle_payment_success(self, data: Dict) -> Dict:
        """Update records for successful payments."""
        payment_data = {
            "status": "completed",
            "amount": data.get("amount", 0) / 100,
            "currency": data.get("currency", "usd").upper(),
            "card_type": data.get("payment_method_details", {}).get("card", {}).get("brand"),
            "stripe_id": data.get("id"),
            "receipt_url": data.get("charges", {}).get("data", [{}])[0].get("receipt_url")
        }
        
        # Update database
        metadata = data
