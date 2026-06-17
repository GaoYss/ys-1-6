import { reactive } from 'vue'

import { purchaseRequestsApi } from '../api/purchaseRequests'

export const prStore = reactive({
  list: [],
  loading: false,
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
  }
})
