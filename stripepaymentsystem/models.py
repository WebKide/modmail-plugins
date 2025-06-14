from typing import Dict, List, Optional
import datetime

class StripeDatabase:
    """Handles data storage using Modmail's plugin database"""
    
    def __init__(self, plugin_partition):
        self.db = plugin_partition

    # Saved Templates (Max allowed=30)
    async def add_template(self, creator_id: int, name: str, amount: float, 
                         description: str, is_test_mode: bool) -> Optional[Dict]:
        """Add a payment template. Returns None if limit (30) reached."""
        templates = await self.db.find_one({"_id": "templates"})
        if not templates:
            templates = {"_id": "templates", "entries": []}
            await self.db.insert_one(templates)
        
        if len(templates["entries"]) >= 30:
            return None
        
        template = {
            "id": len(templates["entries"]) + 1,
            "creator_id": creator_id,
            "name": name,
            "amount": amount,
            "currency": "USD",
            "description": description,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "is_test_mode": is_test_mode
        }
        templates["entries"].append(template)
        await self.db.update_one({"_id": "templates"}, {"$set": templates})
        return template

    async def get_templates(self, creator_id: Optional[int] = None) -> List[Dict]:
        """Fetch all templates or filter by creator."""
        templates = await self.db.find_one({"_id": "templates"})
        if not templates:
            return []
        if creator_id:
            return [t for t in templates["entries"] if t["creator_id"] == creator_id]
        return templates["entries"]

    async def delete_template(self, template_id: int) -> bool:
        """Delete a template by ID. Returns success status."""
        templates = await self.db.find_one({"_id": "templates"})
        if not templates:
            return False
        
        for i, t in enumerate(templates["entries"]):
            if t["id"] == template_id:
                templates["entries"].pop(i)
                await self.db.update_one({"_id": "templates"}, {"$set": templates})
                return True
        return False

    # Payment History
    async def log_payment(self, user_id: int, mod_id: int, thread_id: int,
                        amount: float, product: str, status: str,
                        stripe_id: str, card_type: str, is_test_mode: bool) -> Dict:
        """Record a payment transaction."""
        payment = {
            "user_id": user_id,
            "mod_id": mod_id,
            "thread_id": thread_id,
            "amount": amount,
            "currency": "USD",
            "product": product,
            "status": status,
            "stripe_id": stripe_id,
            "card_type": card_type,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "is_test_mode": is_test_mode
        }
        await self.db.insert_one(payment)
        return payment

    async def get_payments(self, user_id: Optional[int] = None,
                          mod_id: Optional[int] = None, limit: int = 20) -> List[Dict]:
        """Query payment history with optional filters."""
        query = {}
        if user_id:
            query["user_id"] = user_id
        if mod_id:
            query["mod_id"] = mod_id
        
        cursor = self.db.find(query).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def update_payment_status(self, stripe_id: str, new_status: str) -> bool:
        """Update a payment's status (e.g., 'pending' → 'completed')."""
        result = await self.db.update_one(
            {"stripe_id": stripe_id},
            {"$set": {"status": new_status}}
        )
        return result.modified_count > 0
