<template>
  <section>
    <PageHeader eyebrow="Purchase Requests" title="采购申请">
      <div class="header-actions">
        <label class="role-selector">
          当前身份
          <select v-model="currentUser">
            <option value="李店员">李店员（店员）</option>
            <option value="王店长">王店长（店长）</option>
          </select>
        </label>
        <button class="primary-btn" @click="openCreateForm">新建申请</button>
      </div>
    </PageHeader>

    <div class="filter-bar">
      <select v-model="filterStatus" @change="loadList">
        <option value="">全部状态</option>
        <option value="pending_approval">待审批</option>
        <option value="approved">已通过</option>
        <option value="rejected">已驳回</option>
      </select>
    </div>

    <div class="content-grid">
      <section class="panel request-list-panel">
        <h2>申请列表</h2>
        <DataTable :columns="listColumns" :rows="filteredRequests">
          <template #status="{ row }">
            <StatusBadge :label="requestStatusText(row.status)" :variant="requestStatusVariant(row.status)" />
          </template>
          <template #totalAmount="{ row }">¥{{ row.totalAmount.toFixed(2) }}</template>
          <template #actions="{ row }">
            <div class="action-btns">
              <button class="secondary-btn btn-sm" @click="viewDetail(row)">查看</button>
              <button
                v-if="row.status === 'rejected' && row.applicant === currentUser"
                class="secondary-btn btn-sm"
                @click="openEditForm(row)"
              >修改重提</button>
              <button
                v-if="row.status === 'pending_approval' && row.applicant !== currentUser"
                class="primary-btn btn-sm"
                @click="openApprovalDialog(row, 'approve')"
              >审批</button>
              <button
                v-if="row.status === 'pending_approval' && row.applicant !== currentUser"
                class="danger-btn btn-sm"
                @click="openApprovalDialog(row, 'reject')"
              >驳回</button>
            </div>
          </template>
        </DataTable>
      </section>

      <section v-if="selectedRequest" class="panel detail-panel">
        <h2>申请详情</h2>
        <div class="detail-fields">
          <div class="detail-field"><span>申请单号</span><strong>{{ selectedRequest.requestNo }}</strong></div>
          <div class="detail-field"><span>供应商</span><strong>{{ selectedRequest.supplierName }}</strong></div>
          <div class="detail-field"><span>申请人</span><strong>{{ selectedRequest.applicant }}</strong></div>
          <div class="detail-field"><span>状态</span><StatusBadge :label="requestStatusText(selectedRequest.status)" :variant="requestStatusVariant(selectedRequest.status)" /></div>
          <div class="detail-field"><span>预计到货</span><strong>{{ selectedRequest.expectedDate || '-' }}</strong></div>
          <div class="detail-field"><span>备注</span><strong>{{ selectedRequest.remark || '-' }}</strong></div>
          <div class="detail-field"><span>总金额</span><strong>¥{{ selectedRequest.totalAmount.toFixed(2) }}</strong></div>
        </div>

        <h3 style="margin-top: 18px;">申请明细</h3>
        <DataTable :columns="itemColumns" :rows="selectedRequest.items">
          <template #amount="{ row }">¥{{ row.amount.toFixed(2) }}</template>
        </DataTable>

        <h3 style="margin-top: 18px;">审批记录</h3>
        <div v-if="!selectedRequest.approvals.length" class="empty-cell">暂无审批记录</div>
        <div v-else class="approval-timeline">
          <div
            v-for="approval in selectedRequest.approvals"
            :key="approval.id"
            class="approval-item"
            :class="approval.decision"
          >
            <div class="approval-dot"></div>
            <div class="approval-content">
              <div class="approval-header">
                <strong>{{ approval.approver }}</strong>
                <StatusBadge
                  :label="approval.decision === 'approved' ? '通过' : '驳回'"
                  :variant="approval.decision === 'approved' ? 'success' : 'danger'"
                />
              </div>
              <div class="approval-meta">
                <span>申请人：{{ approval.applicant }}</span>
                <span>{{ formatDateTime(approval.createdAt) }}</span>
              </div>
              <div v-if="approval.opinion" class="approval-opinion">{{ approval.opinion }}</div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal">
        <h2>{{ isEditing ? '修改采购申请' : '新建采购申请' }}</h2>
        <div class="form-grid">
          <label>
            申请单号
            <input v-model="form.requestNo" :disabled="isEditing" />
          </label>
          <label>
            供应商
            <select v-model.number="form.supplierId">
              <option disabled :value="null">选择供应商</option>
              <option v-for="s in suppliers" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </label>
          <label>
            预计到货
            <input v-model="form.expectedDate" type="date" />
          </label>
          <label>
            备注
            <input v-model="form.remark" />
          </label>
        </div>

        <div class="line-editor">
          <select v-model.number="line.ingredientId">
            <option disabled :value="null">选择原料</option>
            <option v-for="item in ingredients" :key="item.id" :value="item.id">
              {{ item.name }} / {{ item.unit }}
            </option>
          </select>
          <input v-model.number="line.quantity" type="number" min="1" placeholder="数量" />
          <input v-model.number="line.unitPrice" type="number" min="0" placeholder="单价" />
          <button class="secondary-btn" @click="addLine">添加明细</button>
        </div>

        <DataTable :columns="itemColumns" :rows="form.items">
          <template #amount="{ row }">¥{{ (row.quantity * row.unitPrice).toFixed(2) }}</template>
          <template #ingredientName="{ row }">{{ ingredientName(row.ingredientId) }}</template>
          <template #actions="{ row, index }">
            <button class="danger-btn btn-sm" @click="removeLine(index)">删除</button>
          </template>
        </DataTable>

        <div class="modal-footer">
          <button class="secondary-btn" @click="closeForm">取消</button>
          <button class="primary-btn" @click="submitForm">{{ isEditing ? '修改并重提' : '提交申请' }}</button>
        </div>
      </div>
    </div>

    <div v-if="showApprovalModal" class="modal-overlay" @click.self="closeApprovalDialog">
      <div class="modal">
        <h2>{{ approvalAction === 'approve' ? '审批通过' : '驳回申请' }}</h2>
        <div class="approval-summary">
          <p><strong>申请单号：</strong>{{ approvalTarget.requestNo }}</p>
          <p><strong>申请人：</strong>{{ approvalTarget.applicant }}</p>
          <p><strong>供应商：</strong>{{ approvalTarget.supplierName }}</p>
          <p><strong>总金额：</strong>¥{{ approvalTarget.totalAmount.toFixed(2) }}</p>
        </div>
        <label v-if="approvalAction === 'reject'" class="full-label">
          审批意见 <span class="error-text">*</span>
          <textarea v-model="approvalOpinion" rows="3" placeholder="请填写驳回原因"></textarea>
        </label>
        <label v-else class="full-label">
          审批意见
          <textarea v-model="approvalOpinion" rows="3" placeholder="可选填写审批意见"></textarea>
        </label>
        <div v-if="approvalError" class="error-text">{{ approvalError }}</div>
        <div class="modal-footer">
          <button class="secondary-btn" @click="closeApprovalDialog">取消</button>
          <button
            :class="approvalAction === 'approve' ? 'primary-btn' : 'danger-btn'"
            @click="handleApproval"
          >{{ approvalAction === 'approve' ? '确认通过' : '确认驳回' }}</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { inventoryApi } from '../api/inventory'
import { purchaseRequestsApi } from '../api/purchaseRequests'
import DataTable from '../components/DataTable.vue'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { formatDateTime } from '../utils/format'

const currentUser = ref('李店员')
const filterStatus = ref('')
const requests = ref([])
const suppliers = ref([])
const ingredients = ref([])
const selectedRequest = ref(null)

const showForm = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const form = reactive({
  requestNo: '',
  supplierId: null,
  expectedDate: '',
  remark: '',
  items: []
})
const line = reactive({ ingredientId: null, quantity: 1, unitPrice: 0 })

const showApprovalModal = ref(false)
const approvalAction = ref('approve')
const approvalTarget = ref({})
const approvalOpinion = ref('')
const approvalError = ref('')

const listColumns = [
  { key: 'requestNo', label: '申请单号' },
  { key: 'supplierName', label: '供应商' },
  { key: 'applicant', label: '申请人' },
  { key: 'status', label: '状态' },
  { key: 'totalAmount', label: '金额' },
  { key: 'actions', label: '操作' }
]
const itemColumns = [
  { key: 'ingredientName', label: '原料' },
  { key: 'quantity', label: '数量' },
  { key: 'unitPrice', label: '单价' },
  { key: 'amount', label: '小计' },
  { key: 'actions', label: '操作' }
]

const filteredRequests = computed(() => {
  if (!filterStatus.value) return requests.value
  return requests.value.filter((r) => r.status === filterStatus.value)
})

function requestStatusText(status) {
  const map = {
    pending_approval: '待审批',
    approved: '已通过',
    rejected: '已驳回'
  }
  return map[status] || status
}

function requestStatusVariant(status) {
  const map = {
    pending_approval: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return map[status] || 'neutral'
}

function ingredientName(id) {
  return ingredients.value.find((item) => item.id === id)?.name || '-'
}

function addLine() {
  if (!line.ingredientId || !line.quantity) return
  form.items.push({ id: Date.now(), ...line })
  Object.assign(line, { ingredientId: null, quantity: 1, unitPrice: 0 })
}

function removeLine(index) {
  form.items.splice(index, 1)
}

function openCreateForm() {
  isEditing.value = false
  editingId.value = null
  Object.assign(form, {
    requestNo: `PR${new Date().toISOString().slice(0, 10).replaceAll('-', '')}${Date.now().toString().slice(-3)}`,
    supplierId: null,
    expectedDate: '',
    remark: '',
    items: []
  })
  showForm.value = true
}

function openEditForm(row) {
  isEditing.value = true
  editingId.value = row.id
  Object.assign(form, {
    requestNo: row.requestNo,
    supplierId: row.supplierId,
    expectedDate: row.expectedDate || '',
    remark: row.remark || '',
    items: row.items.map((item) => ({ ...item }))
  })
  showForm.value = true
}

function closeForm() {
  showForm.value = false
}

async function submitForm() {
  if (!form.supplierId || !form.items.length) return
  try {
    if (isEditing.value) {
      await purchaseRequestsApi.update(editingId.value, {
        supplierId: form.supplierId,
        expectedDate: form.expectedDate,
        remark: form.remark,
        items: form.items.map((item) => ({
          ingredientId: item.ingredientId,
          quantity: item.quantity,
          unitPrice: item.unitPrice
        }))
      })
      await purchaseRequestsApi.submit(editingId.value, currentUser.value)
    } else {
      await purchaseRequestsApi.create({
        ...form,
        applicant: currentUser.value,
        items: form.items.map((item) => ({
          ingredientId: item.ingredientId,
          quantity: item.quantity,
          unitPrice: item.unitPrice
        }))
      })
    }
    closeForm()
    await loadList()
  } catch (err) {
    const msg = err.response?.data?.error || '操作失败'
    alert(msg)
  }
}

function viewDetail(row) {
  selectedRequest.value = row
}

function openApprovalDialog(row, action) {
  approvalTarget.value = row
  approvalAction.value = action
  approvalOpinion.value = ''
  approvalError.value = ''
  showApprovalModal.value = true
}

function closeApprovalDialog() {
  showApprovalModal.value = false
}

async function handleApproval() {
  if (approvalAction.value === 'reject' && !approvalOpinion.value.trim()) {
    approvalError.value = '驳回时必须填写审批意见'
    return
  }
  try {
    const targetId = approvalTarget.value.id
    if (approvalAction.value === 'approve') {
      await purchaseRequestsApi.approve(targetId, currentUser.value, approvalOpinion.value)
    } else {
      await purchaseRequestsApi.reject(targetId, currentUser.value, approvalOpinion.value)
    }
    closeApprovalDialog()
    await loadList()
    const refreshed = requests.value.find((r) => r.id === targetId)
    if (refreshed) {
      selectedRequest.value = refreshed
    }
  } catch (err) {
    approvalError.value = err.response?.data?.error || '操作失败'
  }
}

async function loadList() {
  const res = await purchaseRequestsApi.list()
  requests.value = res.data
  if (selectedRequest.value) {
    const refreshed = requests.value.find((r) => r.id === selectedRequest.value.id)
    if (refreshed) {
      selectedRequest.value = refreshed
    }
  }
}

onMounted(async () => {
  const [optionsRes] = await Promise.all([inventoryApi.options(), loadList()])
  ingredients.value = optionsRes.data.ingredients
  suppliers.value = optionsRes.data.suppliers
})
</script>
