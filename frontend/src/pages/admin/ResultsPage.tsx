import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { adminAPI, studentAPI, teacherAPI, exportAPI } from "@/api";
import { useAuthStore } from "@/store/authStore";
import { FiDownloadCloud, FiRefreshCcw } from "react-icons/fi";

interface ResultRow {
  result_id: number;
  student_name?: string;
  student_cccd?: string;
  class_name?: string;
  school_name?: string;
  session_name: string;
  subject_name: string;
  score: number | null;
  grade?: string;
  status?: string;
  published?: boolean;
  published_date?: string;
}

interface Session {
  exam_session_id: number;
  session_name: string;
  is_locked?: boolean;
}

export default function ResultsPage() {
  const { user } = useAuthStore();
  const [results, setResults] = useState<ResultRow[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [loading, setLoading] = useState(true);

  const isAdmin = user?.role === "admin";
  const isTeacher = user?.role === "teacher";

  const fetchData = async () => {
    try {
      if (isAdmin) {
        const [resultsResponse, sessionsResponse] = await Promise.all([
          adminAPI.getResults(sessionId ? Number(sessionId) : undefined),
          adminAPI.getExamSessions(),
        ]);
        setResults(resultsResponse.data.data || []);
        setSessions(sessionsResponse.data.data || []);
      } else if (isTeacher) {
        // Giáo viên chỉ xem kết quả của trường mình, không phân biệt kỳ thi
        const schoolId = await teacherAPI.getMySchoolId(user.user_id);
        const response = await teacherAPI.getSchoolResults(Number(schoolId));
        const sessionsResponse = await teacherAPI.getExamSessions();
        setResults(response.data.results || []);
        setSessions(sessionsResponse.data.data || []);
      } else {
        const response = await studentAPI.getResults();
        setResults(response.data.results || []);
      }
    } catch (error: any) {
      toast.error(error.response?.data?.error || "Không thể tải kết quả");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [sessionId]);

  const publishResults = async () => {
    if (!sessionId) {
      toast.error("Chọn kỳ thi trước khi công bố");
      return;
    }
    try {
      await adminAPI.publishResults(Number(sessionId));
      toast.success("Đã công bố kết quả và khóa đăng nhập thí sinh");
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.error || "Không thể công bố kết quả");
    }
  };

  if (loading) return <div className="text-center py-8">Đang tải...</div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {isAdmin ? "Quản Lý Kết Quả" : "Kết Quả Thi"}
          </h1>
          <p className="text-gray-500 mt-1">
            Theo dõi điểm, trạng thái công bố và khóa sau kỳ thi.
          </p>
        </div>
        <div className="flex gap-3">
          <select
            title="selectExamSession"
            className="input-field w-64"
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value)}
          >
            <option value="">Tất cả kỳ thi</option>
            {sessions.map((session) => (
              <option
                key={session.exam_session_id}
                value={session.exam_session_id}
              >
                {session.session_name}
              </option>
            ))}
          </select>
          {isAdmin && (
            <button
              type="submit"
              className="btn-primary"
              onClick={publishResults}
            >
              Công bố kết quả
            </button>
          )}
          {isTeacher && results.length > 0 && (
            <div>
              <button
                type="button"
                className="btn-primary flex items-center gap-2 text-sm"
                onClick={fetchData}
              >
                <FiRefreshCcw /> Tải lại kết quả
              </button>
              <button
                type="button"
                className="btn-secondary flex items-center gap-2 text-sm"
                onClick={() =>
                  exportAPI.exportSchoolResults(
                    "xlsx",
                    sessionId ? { exam_session_id: Number(sessionId) } : {},
                  )
                }
              >
                <FiDownloadCloud /> Tải xuống kết quả
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50">
                {(isAdmin || isTeacher) && (
                  <th className="text-left py-3 px-4">Thí sinh</th>
                )}
                <th className="text-left py-3 px-4">Kỳ thi</th>
                <th className="text-left py-3 px-4">Môn</th>
                <th className="text-left py-3 px-4">Điểm</th>
                <th className="text-left py-3 px-4">Trạng thái</th>
                {isAdmin && <th className="text-left py-3 px-4">Công bố</th>}
              </tr>
            </thead>
            <tbody>
              {results.map((result, index) => (
                <tr
                  key={result.result_id || index}
                  className="border-b hover:bg-gray-50"
                >
                  {isAdmin && (
                    <td className="py-3 px-4">
                      <div className="font-medium">{result.student_name}</div>
                      <div className="text-xs text-gray-500">
                        {result.student_cccd} - {result.school_name}
                      </div>
                    </td>
                  )}
                  {isTeacher && (
                    <td className="py-3 px-4">
                      <div className="font-medium">{result.student_name}</div>
                      <div className="text-xs text-gray-500">
                        {result.student_cccd} - {result.class_name}
                      </div>
                    </td>
                  )}
                  <td className="py-3 px-4">{result.session_name}</td>
                  <td className="py-3 px-4">{result.subject_name}</td>
                  <td className="py-3 px-4 font-semibold">
                    {result.score ?? "Chưa có"}
                  </td>
                  <td className="py-3 px-4">
                    {result.status || result.grade || "-"}
                  </td>
                  {isAdmin && (
                    <td className="py-3 px-4">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${result.published ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}
                      >
                        {result.published ? "Đã công bố" : "Chưa công bố"}
                      </span>
                    </td>
                  )}
                </tr>
              ))}
              {results.length === 0 && (
                <tr>
                  <td
                    className="py-6 px-4 text-gray-500"
                    colSpan={isAdmin ? 6 : 4}
                  >
                    Chưa có kết quả
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
