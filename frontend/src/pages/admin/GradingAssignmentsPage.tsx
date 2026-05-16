import React, { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { adminAPI } from '@/api'
import { FiEdit, FiTrash2, FiUserPlus, FiXCircle } from 'react-icons/fi'

interface GraderAssignment {
  grade_id: number
  grader_id: number
  grader_name: string
  grading_order: number
  status: string
  score: number | null
}

interface EssayResponse {
  response_id: number
  attempt_id: number
  student_name: string
  student_school_id: number
  question_number: number
  subject_name: string
  graders: GraderAssignment[]
}

export default function GradingAssignmentsPage() {
  const [sessions, setSessions] = useState<any[]>([])
  const [sessionId, setSessionId] = useState('')
  const [assignments, setAssignments] = useState<EssayResponse[]>([])
  const [gradersList, setGradersList] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const [showModal, setShowModal] = useState(false)
  const [targetSlot, setTargetSlot] = useState<{responseId: number, order: number, studentSchoolId: number} | null>(null)
  const [selectedGraderId, setSelectedGraderId] = useState('')

  useEffect(() => {
    adminAPI.getExamSessions().then(res => {
      setSessions(res.data.data || [])
    }).catch(console.error)
    
    adminAPI.getEligibleGraders().then(res => {
      setGradersList(res.data.data || [])
    }).catch(console.error)
  }, [])

  useEffect(() => {
    if (!sessionId) {
      setAssignments([]); return
    }
    fetchAssignments()
  }, [sessionId])

  const fetchAssignments = async () => {
    setLoading(true)
    try {
      const res = await adminAPI.getEssayAssignments(Number(sessionId))
      setAssignments(res.data.data || [])
    } catch (error) {
      toast.error('Lỗi khi tải danh sách bài làm')
    } finally {
      setLoading(false)
    }
  }

  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!targetSlot || !selectedGraderId) return
    
    try {
      await adminAPI.assignGrader({
        response_id: targetSlot.responseId,
        grader_id: Number(selectedGraderId),
        grading_order: targetSlot.order
      })
      toast.success('Đã lưu phân công!')
      setShowModal(false)
      fetchAssignments()
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Lỗi phân công')
    }
  }

  const handleRemove = async (gradeId: number) => {
    if (!confirm('Bạn muốn thu hồi bài chấm này từ giám khảo?')) return
    try {
      await adminAPI.removeGraderAssignment(gradeId)
      toast.success('Đã thu hồi!')
      fetchAssignments()
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Lỗi thu hồi')
    }
  }

  const renderSlot = (response: EssayResponse, order: number) => {
    const grade = response.graders.find(g => g.grading_order === order)
    if (grade) {
      return (
        <div className="flex flex-col gap-1 text-sm bg-gray-50 border p-2 rounded relative group">
           <span className="font-bold text-gray-800">{grade.grader_name}</span>
           {grade.status === 'completed' 
             ? <span className="text-green-600 font-medium">Hoàn thành ({grade.score} điểm)</span> 
             : <span className="text-orange-500 font-medium italic">Chờ chấm...</span>}
             
           {grade.status !== 'completed' && (
             <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 flex gap-1 transition-opacity">
                <button onClick={() => { setTargetSlot({responseId: response.response_id, order, studentSchoolId: response.student_school_id}); setSelectedGraderId(grade.grader_id.toString()); setShowModal(true) }} className="p-1 bg-white border rounded hover:text-blue-600"><FiEdit size={12}/></button>
                <button onClick={() => handleRemove(grade.grade_id)} className="p-1 bg-white border rounded hover:text-red-600"><FiTrash2 size={12}/></button>
             </div>
           )}
        </div>
      )
    }
    return (
      <button onClick={() => { setTargetSlot({responseId: response.response_id, order, studentSchoolId: response.student_school_id}); setSelectedGraderId(''); setShowModal(true) }} 
              className="w-full h-full min-h-12 border-2 border-dashed border-gray-200 rounded text-gray-400 hover:text-blue-600 hover:border-blue-400 hover:bg-blue-50 flex items-center justify-center gap-1 text-xs font-medium transition-colors">
        <FiUserPlus /> Chọn GK {order}
      </button>
    )
  }

  return (
    <div className="space-y-6 text-left">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Phân Công Chấm Thi</h1>
          <p className="text-gray-500 mt-1">Điều phối và gán bài tự luận cho giám khảo Ngữ Văn.</p>
        </div>
        <select className="input-field w-64 bg-white" value={sessionId} onChange={(e) => setSessionId(e.target.value)}>
          <option value="">-- Chọn Kỳ Thi --</option>
          {sessions.map(s => <option key={s.exam_session_id} value={s.exam_session_id}>{s.session_name}</option>)}
        </select>
      </div>

      <div className="card p-0 overflow-hidden">
        {loading ? <div className="p-10 text-center text-gray-500">Đang tải...</div> : (
          <table className="w-full text-sm">
            <thead className="bg-gray-100 border-b">
              <tr>
                 <th className="py-3 px-4 font-bold text-gray-700">Bài thi (Ẩn danh)</th>
                 <th className="py-3 px-4 font-bold text-gray-700 w-48 text-center">Giám khảo 1</th>
                 <th className="py-3 px-4 font-bold text-gray-700 w-48 text-center">Giám khảo 2</th>
                 <th className="py-3 px-4 font-bold text-gray-700 w-48 text-center">GK 3 (Phúc khảo)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {assignments.map(a => (
                <tr key={a.response_id} className="hover:bg-gray-50">
                   <td className="py-3 px-4">
                     <p className="font-bold text-blue-900">{a.subject_name}</p>
                     <p className="text-gray-500 font-medium">Câu tự luận số {a.question_number} - Của CCCD: {a.student_name}</p>
                   </td>
                   <td className="py-2 px-2 align-top">{renderSlot(a, 1)}</td>
                   <td className="py-2 px-2 align-top">{renderSlot(a, 2)}</td>
                   <td className="py-2 px-2 align-top">{renderSlot(a, 3)}</td>
                </tr>
              ))}
              {assignments.length === 0 && sessionId && <tr><td colSpan={4} className="py-12 text-center text-gray-500">Chưa có bài tự luận nào được nộp trong kỳ thi này.</td></tr>}
              {!sessionId && <tr><td colSpan={4} className="py-12 text-center text-gray-400 italic">Vui lòng chọn kỳ thi để xem phân công.</td></tr>}
            </tbody>
          </table>
        )}
      </div>

      {showModal && targetSlot && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg overflow-hidden">
             <div className="px-6 py-4 border-b flex justify-between items-center bg-gray-50">
                <h3 className="text-lg font-bold text-gray-900">Phân Công Giám Khảo {targetSlot.order}</h3>
                <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-red-500"><FiXCircle size={24}/></button>
             </div>
             <form onSubmit={handleAssign} className="p-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">Chọn Giám khảo Ngữ Văn:</label>
                <select className="input-field mb-4" value={selectedGraderId} onChange={e => setSelectedGraderId(e.target.value)} required>
                   <option value="">-- Chọn giáo viên --</option>
                   {gradersList.map(g => {
                     const isSameSchool = g.school_id === targetSlot.studentSchoolId;
                     return (
                       <option key={g.user_id} value={g.user_id} className={isSameSchool ? 'text-red-500 font-bold bg-red-50' : ''}>
                         {g.full_name} ({g.school_name}) {isSameSchool ? ' ⚠️ Trùng trường' : ''}
                       </option>
                     )
                   })}
                </select>
                <div className="flex justify-end gap-3 pt-4 border-t">
                   <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Hủy</button>
                   <button type="submit" className="btn-primary" disabled={!selectedGraderId}>Lưu phân công</button>
                </div>
             </form>
          </div>
        </div>
      )}
    </div>
  )
}