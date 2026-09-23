import axios from "axios"
import { useAuthStore } from "@/store/auth"

const h = () => ({ Authorization: `Bearer ${useAuthStore.getState().token}` })

export const academicApi = {
  programs: () => axios.get("/api/academic/programs", { headers: h() }).then(r => r.data),
  enrollments: (p: Record<string,unknown>) =>
    axios.get("/api/academic/enrollments", { headers: h(), params: p }).then(r => r.data),
  enroll: (d: unknown) => axios.post("/api/academic/enrollments", d, { headers: h() }).then(r => r.data),
  checkPrereqs: (d: unknown) =>
    axios.post("/api/academic/enrollments/prerequisites/check", d, { headers: h() }).then(r => r.data),
  submitGrade: (d: unknown) =>
    axios.post("/api/academic/enrollments/grades", d, { headers: h() }).then(r => r.data),
}

export const tutoringApi = {
  list: (p?: Record<string,unknown>) =>
    axios.get("/api/tutoring/assignments", { headers: h(), params: p }).then(r => r.data),
  create: (d: unknown) => axios.post("/api/tutoring/assignments", d, { headers: h() }).then(r => r.data),
  get: (id: string) => axios.get(`/api/tutoring/assignments/${id}`, { headers: h() }).then(r => r.data),
  respond: (id: string, d: unknown) =>
    axios.post(`/api/tutoring/assignments/${id}/respond`, d, { headers: h() }).then(r => r.data),
  workload: (tutorId: string) =>
    axios.get(`/api/tutoring/assignments/tutor/${tutorId}/workload`, { headers: h() }).then(r => r.data),
  addCoTutor: (d: unknown) =>
    axios.post("/api/tutoring/assignments/co-tutors", d, { headers: h() }).then(r => r.data),
  formCommittee: (id: string, members: unknown[]) =>
    axios.post(`/api/tutoring/assignments/${id}/committee`, members, { headers: h() }).then(r => r.data),
}

export const notifyApi = {
  send: (d: unknown) =>
    axios.post("/api/notifications/notifications", d, { headers: h() }).then(r => r.data),
}
