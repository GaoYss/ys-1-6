from datetime import datetime

from ..extensions import db
from .order import PurchaseOrder, PurchaseOrderItem


class PurchaseRequest(db.Model):
    __tablename__ = "purchase_requests"

    id = db.Column(db.Integer, primary_key=True)
    request_no = db.Column(db.String(40), nullable=False, unique=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending_approval")
    expected_date = db.Column(db.Date, nullable=True)
    remark = db.Column(db.String(255), nullable=True)
    applicant = db.Column(db.String(40), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    supplier = db.relationship("Supplier")
    items = db.relationship(
        "PurchaseRequestItem", cascade="all, delete-orphan", back_populates="request"
    )
    approvals = db.relationship(
        "PurchaseRequestApproval",
        cascade="all, delete-orphan",
        back_populates="request",
        order_by="PurchaseRequestApproval.created_at",
    )

    @property
    def total_amount(self):
        return sum(item.quantity * item.unit_price for item in self.items)

    @property
    def current_approval(self):
        if self.approvals:
            return self.approvals[-1]
        return None

    def submit(self, applicant):
        self.applicant = applicant
        self.status = "pending_approval"
        return self

    def approve(self, approver, opinion=None):
        approval = PurchaseRequestApproval(
            request_id=self.id,
            applicant=self.applicant,
            approver=approver,
            decision="approved",
            opinion=opinion,
        )
        self.approvals.append(approval)
        self.status = "approved"
        return self

    def reject(self, approver, opinion=None):
        approval = PurchaseRequestApproval(
            request_id=self.id,
            applicant=self.applicant,
            approver=approver,
            decision="rejected",
            opinion=opinion,
        )
        self.approvals.append(approval)
        self.status = "rejected"
        return self

    def create_purchase_order(self):
        if self.status != "approved":
            return None
        order = PurchaseOrder(
            order_no=f"PO{self.request_no}",
            supplier_id=self.supplier_id,
            status="pending",
            expected_date=self.expected_date,
            remark=self.remark,
        )
        for item in self.items:
            order.items.append(
                PurchaseOrderItem(
                    ingredient_id=item.ingredient_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                )
            )
        return order

    def to_dict(self):
        return {
            "id": self.id,
            "requestNo": self.request_no,
            "supplierId": self.supplier_id,
            "supplierName": self.supplier.name if self.supplier else None,
            "status": self.status,
            "expectedDate": self.expected_date.isoformat() if self.expected_date else None,
            "remark": self.remark,
            "applicant": self.applicant,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "totalAmount": self.total_amount,
            "items": [item.to_dict() for item in self.items],
            "approvals": [approval.to_dict() for approval in self.approvals],
        }


class PurchaseRequestItem(db.Model):
    __tablename__ = "purchase_request_items"

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(
        db.Integer, db.ForeignKey("purchase_requests.id"), nullable=False
    )
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredients.id"), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    request = db.relationship("PurchaseRequest", back_populates="items")
    ingredient = db.relationship("Ingredient")

    def to_dict(self):
        return {
            "id": self.id,
            "ingredientId": self.ingredient_id,
            "ingredientName": self.ingredient.name if self.ingredient else None,
            "unit": self.ingredient.unit if self.ingredient else None,
            "quantity": self.quantity,
            "unitPrice": self.unit_price,
            "amount": self.quantity * self.unit_price,
        }


class PurchaseRequestApproval(db.Model):
    __tablename__ = "purchase_request_approvals"

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(
        db.Integer, db.ForeignKey("purchase_requests.id"), nullable=False
    )
    applicant = db.Column(db.String(40), nullable=False)
    approver = db.Column(db.String(40), nullable=False)
    decision = db.Column(db.String(20), nullable=False)
    opinion = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    request = db.relationship("PurchaseRequest", back_populates="approvals")

    def to_dict(self):
        return {
            "id": self.id,
            "applicant": self.applicant,
            "approver": self.approver,
            "decision": self.decision,
            "opinion": self.opinion,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
