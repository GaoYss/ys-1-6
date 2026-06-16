import { http } from './http'

export const purchaseRequestsApi = {
  list(params = {}) {
    return http.get('/purchase-requests', { params })
  },
  get(id) {
    return http.get(`/purchase-requests/${id}`)
  },
  create(payload) {
    return http.post('/purchase-requests', payload)
  },
  update(id, payload) {
    return http.put(`/purchase-requests/${id}`, payload)
  },
  submit(id, applicant) {
    return http.post(`/purchase-requests/${id}/submit`, { applicant })
  },
  approve(id, approver, opinion) {
    return http.post(`/purchase-requests/${id}/approve`, { approver, opinion })
  },
  reject(id, approver, opinion) {
    return http.post(`/purchase-requests/${id}/reject`, { approver, opinion })
  }
}
