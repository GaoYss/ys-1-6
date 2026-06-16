from datetime import date

from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models.purchase_request import PurchaseRequest, PurchaseRequestItem

purchase_requests_bp = Blueprint("purchase_requests", __name__)


@purchase_requests_bp.get("")
def list_purchase_requests():
    status = request.args.get("status", "").strip()
    applicant = request.args.get("applicant", "").strip()
    query = PurchaseRequest.query
    if status:
        query = query.filter_by(status=status)
    if applicant:
        query = query.filter_by(applicant=applicant)
    requests = query.order_by(PurchaseRequest.created_at.desc()).all()
    return jsonify([pr.to_dict() for pr in requests])


@purchase_requests_bp.get("/<int:request_id>")
def get_purchase_request(request_id):
    pr = PurchaseRequest.query.get_or_404(request_id)
    return jsonify(pr.to_dict())


@purchase_requests_bp.post("")
def create_purchase_request():
    data = request.get_json() or {}
    expected_date = data.get("expectedDate")
    applicant = data.get("applicant")
    if not applicant:
        return {"error": "申请人不能为空"}, 400
    pr = PurchaseRequest(
        request_no=data["requestNo"],
        supplier_id=data["supplierId"],
        status="pending_approval",
        expected_date=date.fromisoformat(expected_date) if expected_date else None,
        remark=data.get("remark"),
        applicant=applicant,
    )
    for item in data.get("items", []):
        pr.items.append(
            PurchaseRequestItem(
                ingredient_id=item["ingredientId"],
                quantity=float(item["quantity"]),
                unit_price=float(item["unitPrice"]),
            )
        )
    db.session.add(pr)
    db.session.commit()
    return pr.to_dict(), 201


@purchase_requests_bp.put("/<int:request_id>")
def update_purchase_request(request_id):
    pr = PurchaseRequest.query.get_or_404(request_id)
    if pr.status not in ("rejected", "pending_approval"):
        return {"error": "只有被驳回或待审批的申请才能修改"}, 400
    data = request.get_json() or {}
    expected_date = data.get("expectedDate")
    if "supplierId" in data:
        pr.supplier_id = data["supplierId"]
    if expected_date is not None:
        pr.expected_date = date.fromisoformat(expected_date) if expected_date else None
    if "remark" in data:
        pr.remark = data["remark"]
    if "items" in data:
        PurchaseRequestItem.query.filter_by(request_id=pr.id).delete()
        for item in data["items"]:
            pr.items.append(
                PurchaseRequestItem(
                    ingredient_id=item["ingredientId"],
                    quantity=float(item["quantity"]),
                    unit_price=float(item["unitPrice"]),
                )
            )
    db.session.commit()
    return pr.to_dict()


@purchase_requests_bp.post("/<int:request_id>/submit")
def submit_purchase_request(request_id):
    pr = PurchaseRequest.query.get_or_404(request_id)
    if pr.status not in ("rejected", "pending_approval"):
        return {"error": "只有被驳回或待审批的申请才能提交"}, 400
    data = request.get_json() or {}
    applicant = data.get("applicant")
    if not applicant:
        return {"error": "申请人不能为空"}, 400
    pr.submit(applicant)
    db.session.commit()
    return pr.to_dict()


@purchase_requests_bp.post("/<int:request_id>/approve")
def approve_purchase_request(request_id):
    pr = PurchaseRequest.query.get_or_404(request_id)
    if pr.status != "pending_approval":
        return {"error": "只有待审批状态的申请才能审批"}, 400
    data = request.get_json() or {}
    approver = data.get("approver")
    opinion = data.get("opinion")
    if not approver:
        return {"error": "审批人不能为空"}, 400
    if approver == pr.applicant:
        return {"error": "不能审批自己的申请"}, 400
    pr.approve(approver, opinion)
    order = pr.create_purchase_order()
    if order:
        db.session.add(order)
    db.session.commit()
    return pr.to_dict()


@purchase_requests_bp.post("/<int:request_id>/reject")
def reject_purchase_request(request_id):
    pr = PurchaseRequest.query.get_or_404(request_id)
    if pr.status != "pending_approval":
        return {"error": "只有待审批状态的申请才能审批"}, 400
    data = request.get_json() or {}
    approver = data.get("approver")
    opinion = data.get("opinion")
    if not approver:
        return {"error": "审批人不能为空"}, 400
    if approver == pr.applicant:
        return {"error": "不能审批自己的申请"}, 400
    if not opinion:
        return {"error": "驳回时请填写审批意见"}, 400
    pr.reject(approver, opinion)
    db.session.commit()
    return pr.to_dict()
