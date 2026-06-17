import { reactive } from 'vue'

import { purchaseRequestsApi } from '../api/purchaseRequests'

export const prStore = reactive({
  list: [],
  loading: false,
  currentUser: '李店员',
  isManager: false,
  setUser(name) {
    this.currentUser = name
    this.isManager = name.includes('店长')
  },
  async refresh() {
    this.loading = true
    try {
      const res = await purchaseRequestsApi.list()
      this.list = res.data
    } finally {
      this.loading = false
    }
  },
  get pendingCount() {
    return this.list.filter((r) => r.status === 'pending_approval').length
  },
  get pendingCountForCurrentUser() {
    const pending = this.list.filter((r) => r.status === 'pending_approval')
    if (this.isManager) return pending.length
    return pending.filter((r) => r.applicant === this.currentUser).length
  }
})
