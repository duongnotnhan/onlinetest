import React, { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { gradingAPI } from "@/api";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { FiXCircle, FiCheckCircle, FiClock, FiInfo } from "react-icons/fi";

interface Essay {
  essay_grade_id: number;
  question_number: number;
  student_name: string;
  subject: string;
  status: string;
  score: number | null;
  grader_sequence: number;
  submitted_date: string;
}

export default function GradeEssayPage() {
  const [essays, setEssays] = useState<Essay[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"pending" | "completed">(
    "pending",
  );

  const [selectedEssay, setSelectedEssay] = useState<any>(null);
  const [scoreForm, setScoreForm] = useState({ score: "", feedback: "" });
  const [saving, setSaving] = useState(false);

  const fetchEssays = async () => {
    try {
      const response = await gradingAPI.getEssays({ status: activeTab });
      setEssays(response.data.data || []);
    } catch (error) {
      toast.error("Lỗi khi tải danh sách bài thi: " + (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchEssays();
  }, [activeTab]);

  const openGradeModal = async (id: number) => {
    try {
      const res = await gradingAPI.getEssayDetail(id);
      setSelectedEssay(res.data);
      setScoreForm({
        score:
          res.data.current_score !== null &&
          res.data.current_score !== undefined
            ? res.data.current_score.toString()
            : "",
        feedback: res.data.feedback || "",
      });
    } catch (e) {
      toast.error("Không thể tải chi tiết bài làm: " + (e as Error).message);
    }
  };

  const handleSubmitGrade = async (e: React.FormEvent) => {
    e.preventDefault();
    const numericScore = parseFloat(scoreForm.score);
    if (
      isNaN(numericScore) ||
      numericScore < 0 ||
      numericScore > selectedEssay.max_points
    ) {
      return toast.error(`Điểm phải từ 0 đến ${selectedEssay.max_points}`);
    }
    setSaving(true);
    try {
      await gradingAPI.submitGrade(
        selectedEssay.essay_grade_id,
        numericScore,
        scoreForm.feedback,
      );
      toast.success("Chấm điểm thành công!");
      setSelectedEssay(null);
      fetchEssays();
    } catch (error) {
      toast.error("Lỗi lưu điểm: " + (error as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 text-left">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Chấm Tự Luận Ngữ Văn
        </h1>
        <p className="text-gray-500 mt-1">
          Danh sách các bài làm được hệ thống phân công ẩn danh.
        </p>
      </div>

      <div className="flex bg-white border rounded-lg overflow-hidden w-fit">
        <button
          className={`px-6 py-2 font-medium ${activeTab === "pending" ? "bg-blue-600 text-white" : "text-gray-700 hover:bg-gray-50"}`}
          onClick={() => setActiveTab("pending")}
        >
          Cần chấm ({activeTab === "pending" ? essays.length : "..."})
        </button>
        <button
          className={`px-6 py-2 font-medium ${activeTab === "completed" ? "bg-green-600 text-white" : "text-gray-700 hover:bg-gray-50"}`}
          onClick={() => setActiveTab("completed")}
        >
          Đã chấm ({activeTab === "completed" ? essays.length : "..."})
        </button>
      </div>

      <div className="card p-0 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">Đang tải...</div>
        ) : (
          <table className="w-full text-sm text-left">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3">Câu hỏi số</th>
                <th className="px-4 py-3">Lượt chấm</th>
                <th className="px-4 py-3 text-center">Trạng thái</th>
                <th className="px-4 py-3 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {essays.map((essay) => (
                <tr key={essay.essay_grade_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-bold">
                    Câu {essay.question_number}
                  </td>
                  <td className="px-4 py-3">
                    <span className="bg-gray-100 px-2 py-1 rounded">
                      Giám khảo {essay.grader_sequence}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {essay.status === "completed" ? (
                      <span className="text-green-600 flex items-center justify-center gap-1">
                        <FiCheckCircle /> {essay.score ?? 0} điểm
                      </span>
                    ) : (
                      <span className="text-orange-500 flex items-center justify-center gap-1">
                        <FiClock /> Chờ chấm
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => openGradeModal(essay.essay_grade_id)}
                      className="btn-primary py-1 px-3 text-xs"
                    >
                      {essay.status === "completed" ? "Xem lại" : "Chấm bài"}
                    </button>
                  </td>
                </tr>
              ))}
              {essays.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-10 text-center text-gray-500">
                    Tuyệt vời! Không có bài nào trong danh sách này.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* MODAL CHẤM BÀI */}
      {selectedEssay && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-60">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-[1200px] h-[95vh] flex flex-col overflow-hidden">
            <div className="px-6 py-4 border-b flex justify-between items-center bg-gray-50">
              <h3 className="text-xl font-bold text-gray-900">
                Môn {selectedEssay.subject} - Câu{" "}
                {selectedEssay.question_number}
              </h3>
              <button
                title="setSelectedEssay"
                type="button"
                onClick={() => setSelectedEssay(null)}
                className="text-gray-400 hover:text-red-500"
              >
                <FiXCircle size={24} />
              </button>
            </div>

            <div className="flex-1 overflow-hidden flex flex-col md:flex-row">
              {/* Cột trái: Ngữ liệu (nếu có), Đề bài, Bài làm & Đáp án */}
              <div className="flex-1 border-r border-gray-200 overflow-y-auto bg-gray-100 p-6 space-y-6">
                {/* Ngữ liệu chung (Nếu có) */}
                {selectedEssay.reading_material && (
                  <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm">
                    <p className="text-xs font-bold uppercase text-gray-500 mb-2 border-b pb-2">
                      Ngữ liệu chung
                    </p>
                    <div className="prose prose-sm max-w-none text-gray-800">
                      <ReactMarkdown
                        remarkPlugins={[remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                      >
                        {selectedEssay.reading_material}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}

                <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm">
                  <p className="text-xs font-bold uppercase text-gray-500 mb-2 border-b pb-2">
                    Đề bài
                  </p>
                  <div className="prose max-w-none text-gray-900">
                    <ReactMarkdown
                      remarkPlugins={[remarkMath]}
                      rehypePlugins={[rehypeKatex]}
                    >
                      {selectedEssay.question_text}
                    </ReactMarkdown>
                  </div>
                </div>

                <div className="bg-white p-5 rounded-lg border-2 border-blue-200 shadow-sm">
                  <p className="text-xs font-bold uppercase text-blue-600 mb-2 border-b border-blue-100 pb-2 flex items-center justify-between">
                    <span>Bài làm của thí sinh (Ẩn danh)</span>
                    <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                      Giám khảo {selectedEssay.grader_sequence}
                    </span>
                  </p>
                  <div className="whitespace-pre-wrap text-gray-800 text-lg leading-relaxed">
                    {selectedEssay.student_answer || (
                      <span className="text-gray-400 italic">
                        Thí sinh để trống
                      </span>
                    )}
                  </div>
                </div>

                {/* KHỐI HƯỚNG DẪN CHẤM MỚI THÊM VÀO ĐÂY */}
                <div className="bg-green-50 p-5 rounded-lg border border-green-200 shadow-sm">
                  <p className="text-xs font-bold uppercase text-green-700 mb-2 border-b border-green-200 pb-2 flex items-center gap-1">
                    <FiInfo /> Gợi ý / Đáp án từ hệ thống
                  </p>
                  <div className="prose prose-sm max-w-none text-gray-800 bg-white p-4 rounded border border-green-100">
                    {selectedEssay.answer_key ? (
                      <ReactMarkdown
                        remarkPlugins={[remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                      >
                        {selectedEssay.answer_key}
                      </ReactMarkdown>
                    ) : (
                      <span className="text-gray-400 italic">
                        Chưa có hướng dẫn chấm cho câu hỏi này.
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Cột phải: Form nhập điểm */}
              <div className="w-full md:w-80 bg-white p-6 overflow-y-auto">
                <form
                  id="grade-form"
                  onSubmit={handleSubmitGrade}
                  className="space-y-6"
                >
                  <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg text-center shadow-sm">
                    <p className="text-sm font-bold text-blue-900 mb-2">
                      ĐIỂM SỐ (TỐI ĐA: {selectedEssay.max_points})
                    </p>
                    <input
                      title="markScore"
                      type="number"
                      step="0.25"
                      min="0"
                      max={selectedEssay.max_points}
                      className="w-full text-center text-4xl font-black p-4 border-2 border-blue-300 rounded-lg focus:border-blue-600 focus:ring-4 focus:ring-blue-100 outline-none transition-all"
                      value={scoreForm.score}
                      onChange={(e) =>
                        setScoreForm({ ...scoreForm, score: e.target.value })
                      }
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-gray-700 mb-2">
                      Nhận xét (Tùy chọn)
                    </label>
                    <textarea
                      className="input-field min-h-[200px] border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                      placeholder="Nhập phản hồi cho học sinh tại đây..."
                      value={scoreForm.feedback}
                      onChange={(e) =>
                        setScoreForm({ ...scoreForm, feedback: e.target.value })
                      }
                    />
                  </div>
                  <button
                    type="submit"
                    className="btn-primary w-full py-4 text-lg font-black uppercase tracking-wider shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all"
                    disabled={saving}
                  >
                    {saving ? "Đang lưu..." : "Lưu điểm & Đóng"}
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
