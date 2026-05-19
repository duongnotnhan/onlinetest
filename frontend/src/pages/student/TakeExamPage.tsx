import React, { useState, useEffect, useRef, memo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { studentAPI, authAPI } from "@/api";
import toast from "react-hot-toast";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import remarkGfm from "remark-gfm";
import rehypeKatex from "rehype-katex";
import rehypeRaw from "rehype-raw";
// @ts-expect-error - module not found
import "katex/dist/katex.min.css";
import {
  FiCheckCircle,
  FiCheckSquare,
  FiSquare,
  FiMaximize2,
  FiMinimize2,
  FiTrash,
} from "react-icons/fi";

const getPartLabel = (subject: string, part: string) => {
  if (subject === "Ngữ Văn") {
    if (part === "part1") return "PHẦN I. ĐỌC HIỂU";
    if (part === "part2") return "PHẦN II. LÀM VĂN";
  }
  if (part === "part1")
    return "PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn";
  if (part === "part2") return "PHẦN II. Câu trắc nghiệm đúng sai";
  if (part === "part3") return "PHẦN III. Câu trắc nghiệm trả lời ngắn";
  if (part.includes("rc"))
    return subject === "Tiếng Anh" ? "READING COMPREHENSION" : "ĐỌC HIỂU";
  if (part.includes("rf"))
    return subject === "Tiếng Anh"
      ? "READING FILL IN THE BLANK"
      : "ĐỌC ĐIỀN TỪ";
  if (part.includes("rs"))
    return subject === "Tiếng Anh" ? "REORDERING SENTENCES" : "SẮP XẾP CÂU";
  return part.toUpperCase();
};

const getTrackLabel = (track: string) => {
  if (track === "computer_science")
    return "PHẦN ĐỊNH HƯỚNG KHOA HỌC MÁY TÍNH (CS)";
  if (track === "applied_informatics")
    return "PHẦN ĐỊNH HƯỚNG TIN HỌC ỨNG DỤNG (ICT)";
  return "A. PHẦN CHUNG (Dành cho tất cả thí sinh)";
};

const countWords = (str: string) => {
  if (!str || str.trim() === "") return 0;
  return str.trim().split(/\s+/).length;
};

// Hàm sinh băng rôn chỉ dẫn, lọc bỏ dải câu con ở cấp Phần để hiển thị chính xác tuyệt đối
function generateInstructionBanner(
  subjectName: string,
  questions: any[],
  customType?: string,
) {
  if (!questions || questions.length === 0) return null;
  const nums = questions
    .map((q) => q.question_number)
    .filter((n) => n !== undefined);
  if (nums.length === 0) return null;
  const minQ = Math.min(...nums);
  const maxQ = Math.max(...nums);
  const isEnglish = subjectName.toLowerCase().includes("tiếng anh");

  if (isEnglish) {
    if (customType === "reading_fill_in") {
      return `Read the following passage and choose A, B, C, or D to indicate the option that best fits each of the numbered blanks from ${minQ} to ${maxQ}.`;
    }
    if (customType === "reading_comprehension") {
      return `Read the following passage and choose A, B, C, or D to indicate the best answer to each of the following questions from ${minQ} to ${maxQ}.`;
    }
    if (customType === "arrangement_correction") {
      return `Choose the letter A, B, C, or D to indicate the best arrangement of utterances or sentences to make a cohesive and coherent exchange or text in each of the following questions from ${minQ} to ${maxQ}.`;
    }
    return `Choose the letter A, B, C, or D to indicate the best answer to each of the following questions from ${minQ} to ${maxQ}.`;
  }

  const qSample = questions[0];
  if (qSample?.type === "true_false") {
    return `Thí sinh trả lời từ câu ${minQ} đến câu ${maxQ}. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai.`;
  }
  if (qSample?.type === "short_answer") {
    return `Thí sinh trả lời từ câu ${minQ} đến câu ${maxQ}. Điền chuỗi đáp án hợp lệ vào các ô vuông tương ứng.`;
  }
  if (qSample?.type === "essay") {
    return `Thí sinh trả lời các câu hỏi từ ${minQ} đến ${maxQ} trực tiếp vào phần điền.`;
  }

  return `Thí sinh trả lời từ câu ${minQ} đến câu ${maxQ}. Mỗi câu hỏi thí sinh chỉ chọn một phương án đúng nhất.`;
}

const MarkdownContent = memo(({ content }: { content: string }) => {
  if (!content) return null;

  return (
    <div className="prose max-w-none text-slate-900 text-base leading-relaxed custom-markdown-table">
      <ReactMarkdown
        remarkPlugins={[
          [remarkGfm, { singleTiffe: false, autolink: false }],
          remarkMath,
        ]}
        rehypePlugins={[rehypeRaw, rehypeKatex]}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
});

const ShortAnswerInput = ({
  questionId,
  value,
  onChange,
  disabled,
}: {
  questionId: number;
  value: string;
  onChange: (val: string) => void;
  disabled: boolean;
}) => {
  const chars = (value || "").padEnd(4, " ").split("").slice(0, 4);
  const handleInput = (
    index: number,
    e: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const val = e.target.value.slice(-1);
    if (val) {
      if (!/^[0-9\-,]$/.test(val)) return;
      if (val === "-" && index !== 0) return;
      if (val === "," && (index === 0 || index === 3)) return;
    }
    const newChars = [...chars];
    newChars[index] = val || " ";
    if (!val) {
      for (let j = index + 1; j < 4; j++) newChars[j] = " ";
    }
    onChange(newChars.join(""));
    if (val && index < 3) {
      setTimeout(() => {
        const nextInput = document.getElementById(
          `q_${questionId}_box_${index + 1}`,
        );
        if (nextInput) nextInput.focus();
      }, 50);
    }
  };

  const handleKeyDown = (
    index: number,
    e: React.KeyboardEvent<HTMLInputElement>,
  ) => {
    if (e.key === "Backspace") {
      if (chars[index] === " " && index > 0) {
        setTimeout(() => {
          const prevInput = document.getElementById(
            `q_${questionId}_box_${index - 1}`,
          );
          if (prevInput) prevInput.focus();
        }, 10);
      }
    } else if (e.key === "ArrowLeft" && index > 0) {
      document.getElementById(`q_${questionId}_box_${index - 1}`)?.focus();
    } else if (e.key === "ArrowRight" && index < 3) {
      document.getElementById(`q_${questionId}_box_${index + 1}`)?.focus();
    }
  };

  return (
    <div className="flex gap-2 md:gap-3">
      {[0, 1, 2, 3].map((i) => {
        const isBoxDisabled = disabled || (i > 0 && chars[i - 1] === " ");
        return (
          <input
            title="shortAnswer"
            key={i}
            id={`q_${questionId}_box_${i}`}
            type="text"
            className={`w-11 h-12 md:w-14 md:h-14 text-xl md:text-2xl font-bold text-center border rounded-lg focus:ring-0 outline-none shadow-xs transition-all ${isBoxDisabled ? "bg-slate-100 border-slate-200 text-slate-400 cursor-not-allowed" : "bg-white border-slate-300 focus:border-blue-500 text-slate-900"}`}
            value={chars[i] === " " ? "" : chars[i]}
            onChange={(e) => handleInput(i, e)}
            onKeyDown={(e) => handleKeyDown(i, e)}
            disabled={isBoxDisabled}
            autoComplete="off"
          />
        );
      })}
    </div>
  );
};

export default function TakeExamPage() {
  const { attemptId } = useParams();
  const navigate = useNavigate();

  const [paper, setPaper] = useState<any>(null);
  const [answers, setAnswers] = useState<Record<number, any>>({});
  const [timeLeft, setTimeLeft] = useState<number>(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);

  const [selectedTrack, setSelectedTrack] = useState<string | null>(null);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const endTimeRef = useRef<number | null>(null);

  useEffect(() => {
    const fetchPaper = async () => {
      try {
        const res = await studentAPI.getExamPaper(Number(attemptId));
        setPaper(res.data);
        endTimeRef.current =
          Date.now() + res.data.time_remaining_seconds * 1000;
        setTimeLeft(res.data.time_remaining_seconds);
        if (res.data.saved_answers) setAnswers(res.data.saved_answers);
        if (res.data.selected_informatics_track)
          setSelectedTrack(res.data.selected_informatics_track);
      } catch (error: any) {
        toast.error(error.response?.data?.error || "Không thể tải đề thi");
        navigate("/student/dashboard");
      }
    };
    fetchPaper();
    const keepAlive = setInterval(
      () => {
        authAPI.refreshToken().catch(console.error);
      },
      10 * 60 * 1000,
    );
    return () => clearInterval(keepAlive);
  }, [attemptId, navigate]);

  useEffect(() => {
    if (!paper || result) return;
    const timer = setInterval(() => {
      if (!endTimeRef.current) return;
      const now = Date.now();
      const remaining = Math.max(
        0,
        Math.floor((endTimeRef.current - now) / 1000),
      );
      setTimeLeft(remaining);
      if (remaining <= 0) {
        clearInterval(timer);
        if (!isSubmitting) handleAutoSubmit();
      }
    }, 1000);
    return () => clearInterval(timer);
  }, [paper, result, isSubmitting]);

  const handleAnswerChange = async (questionId: number, value: any) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
    try {
      await studentAPI.submitAnswer(Number(attemptId), questionId, value);
    } catch (error) {
      toast.error("Lỗi lưu tạm: " + (error as Error).message);
    }
  };

  const handleClearAnswer = async (questionId: number) => {
    const newAnswers = { ...answers };
    delete newAnswers[questionId];
    setAnswers(newAnswers);
    try {
      await studentAPI.submitAnswer(Number(attemptId), questionId, null);
    } catch (error) {
      toast.error("Lỗi khi xóa câu trả lời: " + (error as Error).message);
    }
  };

  const handleTrackChange = async (track: string) => {
    setSelectedTrack(track);
    try {
      const firstQInTrack = paper.questions.find(
        (q: any) => q.informatics_track === track,
      );
      if (firstQInTrack)
        await studentAPI.submitAnswer(
          Number(attemptId),
          firstQInTrack.question_id,
          answers[firstQInTrack.question_id] || null,
          track,
        );
    } catch (error) {
      toast.error("Lỗi khi thay đổi track: " + (error as Error).message);
    }
  };

  const handleAutoSubmit = async () => {
    toast.error("Hết giờ làm bài!");
    await submitFinal();
  };
  const handleManualSubmit = async () => {
    if (!confirm("Xác nhận nộp bài sớm?")) return;
    await submitFinal();
  };

  const submitFinal = async () => {
    setIsSubmitting(true);
    try {
      let finalTrack = selectedTrack;
      if (paper.subject_name === "Tin Học" && !finalTrack) {
        let countCS = 0;
        let countICT = 0;
        paper.questions.forEach((q: any) => {
          if (answers[q.question_id]) {
            if (q.informatics_track === "computer_science") countCS++;
            if (q.informatics_track === "applied_informatics") countICT++;
          }
        });
        finalTrack =
          countICT > countCS ? "applied_informatics" : "computer_science";
      }
      for (const q of paper.questions) {
        const track = q.informatics_track || "common";
        if (track !== "common") {
          if (track !== finalTrack)
            await studentAPI.submitAnswer(
              Number(attemptId),
              q.question_id,
              null,
            );
          else if (answers[q.question_id] === undefined)
            await studentAPI.submitAnswer(
              Number(attemptId),
              q.question_id,
              null,
              finalTrack,
            );
        } else if (answers[q.question_id] === undefined)
          await studentAPI.submitAnswer(Number(attemptId), q.question_id, null);
      }
      const res = await studentAPI.submitExam(Number(attemptId));
      setResult(res.data);
      toast.success("Nộp bài thành công!");
    } catch (error) {
      toast.error("Lỗi nộp bài: " + (error as Error).message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h > 0 ? h + ":" : ""}${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const renderExamContent = () => {
    const elements: JSX.Element[] = [];
    let currentPart = "";
    let currentTrack = "";
    let currentSubsectionId: number | null = null;

    const mappedQuestions = paper.questions.map((q: any) => ({
      ...q,
      mappedPart: q.mappedPart || q.part || "part1",
    }));

    paper.questions.forEach((q: any) => {
      const mappedPart = q.mappedPart || q.part || "part1";

      // 1. Gỡ lỗi lặp lại băng rôn: Lọc tuyệt đối chỉ lấy các câu độc lập trực thuộc để tính min/max đầu phần
      if (mappedPart !== currentPart) {
        currentPart = mappedPart;
        currentTrack = "";
        currentSubsectionId = null;
        const looseQsInPart = mappedQuestions.filter(
          (mq: any) => mq.mappedPart === currentPart && !mq.subsection_id,
        );
        const partInstruction = generateInstructionBanner(
          paper.subject_name,
          looseQsInPart,
          undefined,
        );

        elements.push(
          <div key={`part-wrapper-${currentPart}`} className="mt-10 mb-5">
            <h2 className="text-lg md:text-xl font-bold text-blue-900 uppercase border-b border-blue-200 pb-1">
              {getPartLabel(paper.subject_name, currentPart)}
            </h2>
            {partInstruction && (
              <p className="mt-2 text-xs font-medium text-slate-600 bg-white p-2 rounded-lg border border-slate-200 shadow-sm">
                {partInstruction}
              </p>
            )}
          </div>,
        );
      }

      if (paper.subject_name === "Tin Học" && currentPart === "part2") {
        const trackValue = q.informatics_track || "common";
        if (trackValue !== currentTrack) {
          currentTrack = trackValue;
          currentSubsectionId = null;
          elements.push(
            <div
              key={`track-${trackValue}`}
              className={`content-box border-l-4 px-4 py-3 mt-6 mb-4 rounded-r-xl flex items-center justify-between transition-colors cursor-pointer shadow-sm ${trackValue === "common" ? "bg-slate-50 border-blue-600" : selectedTrack === trackValue ? "bg-blue-50 border-blue-600" : selectedTrack ? "bg-slate-50 border-slate-200 opacity-60" : "bg-slate-50 border-slate-300 hover:bg-slate-100"}`}
              onClick={() =>
                trackValue !== "common" ? handleTrackChange(trackValue) : null
              }
            >
              <h3
                className={`text-base font-bold uppercase ${trackValue === "common" ? "text-slate-800" : selectedTrack === trackValue ? "text-blue-900" : "text-slate-600"}`}
              >
                {trackValue === "computer_science"
                  ? "B. "
                  : trackValue === "applied_informatics"
                    ? "C. "
                    : ""}
                {getTrackLabel(trackValue)}
              </h3>
              {trackValue !== "common" && (
                <div
                  className={`text-xs font-bold flex items-center gap-1.5 ${selectedTrack === trackValue ? "text-blue-600" : "text-slate-400"}`}
                >
                  {selectedTrack === trackValue ? (
                    <FiCheckSquare size={20} />
                  ) : (
                    <FiSquare size={20} />
                  )}{" "}
                  {selectedTrack === trackValue
                    ? "ĐÃ CHỌN LÀM"
                    : "CHỌN LÀM PHẦN NÀY"}
                </div>
              )}
            </div>,
          );
        }
      }

      if (q.subsection_id && q.subsection_id !== currentSubsectionId) {
        currentSubsectionId = q.subsection_id;
        const sub = paper.subsections?.find(
          (s: any) => String(s.subsection_id) === String(q.subsection_id),
        );
        if (sub && sub.content) {
          let subContent = sub.content;
          const subQs = mappedQuestions.filter(
            (sq: any) => String(sq.subsection_id) === String(sub.subsection_id),
          );
          if (sub.type === "reading_fill_in") {
            let qIdx = 0;
            subContent = subContent.replace(
              /(?:\(|\[)?\d+(?:\)|\]|\.)?\s*(_{3,})/g,
              (match: any, underscores: any) => {
                const qNum = subQs[qIdx++]?.question_number;
                return qNum ? `(**${qNum}**) ${underscores}` : match;
              },
            );
          }
          const subInstructionBanner = generateInstructionBanner(
            paper.subject_name,
            subQs,
            sub.type,
          );

          elements.push(
            <div
              key={`sub-${sub.subsection_id}`}
              className="content-box bg-indigo-50/20 border-indigo-100 shadow-sm my-5 p-5 space-y-3"
            >
              {subInstructionBanner && (
                <p className="text-xs font-bold text-indigo-950 bg-white p-3 rounded-lg border border-indigo-200 shadow-sm">
                  {subInstructionBanner}
                </p>
              )}
              {sub.title && (
                <h4 className="font-bold text-sm text-indigo-900 uppercase border-b border-indigo-100 pb-1">
                  {sub.title}
                </h4>
              )}
              <div className="content-box p-4 border-slate-200 shadow-sm">
                <MarkdownContent content={subContent} />
              </div>
            </div>,
          );
        }
      } else if (!q.subsection_id) {
        currentSubsectionId = null;
      }

      const safeTrack = q.informatics_track || "common";
      const isTrackDisabled =
        safeTrack !== "common" &&
        selectedTrack !== null &&
        selectedTrack !== safeTrack;

      elements.push(
        <div
          id={`question-${q.question_id}`}
          key={`q-${q.question_id}`}
          className={`content-box p-5 border transition-all mt-3 mb-4 shadow-sm ${isTrackDisabled ? "border-slate-100 opacity-40 pointer-events-none filter grayscale" : "border-slate-200"}`}
        >
          <div className="flex items-center gap-2 mb-4">
            <div
              className={`${isTrackDisabled ? "bg-slate-300" : "bg-blue-600"} text-white font-bold text-sm w-7 h-7 rounded-full flex items-center justify-center shrink-0`}
            >
              {q.question_number}
            </div>
            <div className="font-medium text-slate-500 uppercase tracking-wider text-[11px] bg-slate-50 px-2 py-0.5 rounded border border-slate-100">
              {q.type === "multiple_choice"
                ? "Trắc nghiệm"
                : q.type === "true_false"
                  ? "Đúng Sai"
                  : q.type === "short_answer"
                    ? "Trả lời ngắn"
                    : "Tự luận"}
            </div>
          </div>
          <div className="mb-6 text-slate-900">
            <MarkdownContent content={q.text} />
          </div>

          {q.type === "multiple_choice" && q.choices && (
            <div className="space-y-3 pl-0 md:pl-8">
              {q.choices.map((c: any) => (
                <label
                  key={c.choice_id}
                  className={`content-box p-3 flex items-start gap-3 cursor-pointer transition-all shadow-sm ${answers[q.question_id] === c.choice_label ? "bg-blue-50/50 border-blue-400" : "bg-white hover:bg-slate-50 border-slate-200"}`}
                >
                  <input
                    type="radio"
                    name={`q_${q.question_id}`}
                    value={c.choice_label}
                    checked={answers[q.question_id] === c.choice_label}
                    onChange={(e) =>
                      handleAnswerChange(q.question_id, e.target.value)
                    }
                    className="mt-1 w-4 h-4 text-blue-600 focus:ring-blue-500 cursor-pointer shrink-0"
                    disabled={isTrackDisabled}
                  />
                  <div className="flex-1 text-base mt-0.5 leading-relaxed">
                    <span className="font-black mr-2 text-slate-800 float-left">
                      {c.choice_label}.
                    </span>{" "}
                    <div className="overflow-hidden">
                      <MarkdownContent
                        content={c.choice_text || c.text || c.content || ""}
                      />
                    </div>
                  </div>
                </label>
              ))}
            </div>
          )}

          {q.type === "true_false" && q.items && (
            <div className="space-y-3 pl-0 md:pl-8">
              {q.items.map((item: any) => (
                <div
                  key={item.item_id}
                  className={`content-box p-3 flex flex-col md:flex-row justify-between items-center transition-all gap-4 shadow-sm ${answers[q.question_id]?.[item.item_id] ? "bg-slate-50/50 border-slate-300" : "bg-white border-slate-200"}`}
                >
                  <div className="flex-1 flex gap-3 w-full items-start text-base leading-relaxed">
                    <span className="font-black text-slate-800 mt-0.5 shrink-0">
                      {item.item_label})
                    </span>{" "}
                    <div className="flex-1 overflow-hidden">
                      <MarkdownContent
                        content={item.item_text || item.text || ""}
                      />
                    </div>
                  </div>
                  <div className="bg-slate-50 p-1.5 rounded-lg flex gap-2 shrink-0 border border-slate-200 w-full md:w-auto justify-center">
                    <label
                      className={`flex-1 md:flex-none text-center px-4 py-1.5 rounded-md font-bold text-xs cursor-pointer transition-colors shadow-sm ${answers[q.question_id]?.[item.item_id] === "true" ? "bg-green-600 text-white" : "bg-transparent text-slate-600 hover:bg-white"}`}
                    >
                      <input
                        type="radio"
                        className="hidden"
                        disabled={isTrackDisabled}
                        checked={
                          answers[q.question_id]?.[item.item_id] === "true"
                        }
                        onChange={() =>
                          handleAnswerChange(q.question_id, {
                            ...(answers[q.question_id] || {}),
                            [item.item_id]: "true",
                          })
                        }
                      />{" "}
                      ĐÚNG
                    </label>
                    <label
                      className={`flex-1 md:flex-none text-center px-4 py-1.5 rounded-md font-bold text-xs cursor-pointer transition-colors shadow-sm ${answers[q.question_id]?.[item.item_id] === "false" ? "bg-red-600 text-white" : "bg-transparent text-slate-600 hover:bg-white"}`}
                    >
                      <input
                        type="radio"
                        className="hidden"
                        disabled={isTrackDisabled}
                        checked={
                          answers[q.question_id]?.[item.item_id] === "false"
                        }
                        onChange={() =>
                          handleAnswerChange(q.question_id, {
                            ...(answers[q.question_id] || {}),
                            [item.item_id]: "false",
                          })
                        }
                      />{" "}
                      SAI
                    </label>
                  </div>
                </div>
              ))}
              {answers[q.question_id] &&
                Object.keys(answers[q.question_id]).length > 0 &&
                !isTrackDisabled && (
                  <div className="text-right mt-2">
                    <button
                      onClick={() => handleClearAnswer(q.question_id)}
                      className="text-xs font-bold text-red-500 hover:text-red-700 flex items-center gap-1 ml-auto"
                    >
                      <FiTrash />
                      Xóa lựa chọn
                    </button>
                  </div>
                )}
            </div>
          )}

          {q.type === "short_answer" && (
            <div className="pl-0 md:pl-8 flex flex-col items-start">
              <ShortAnswerInput
                questionId={q.question_id}
                value={answers[q.question_id] || ""}
                onChange={(val) => handleAnswerChange(q.question_id, val)}
                disabled={isTrackDisabled}
              />
              <div className="flex justify-between items-center mt-3 gap-4">
                <p className="text-xs text-slate-500 flex items-center gap-1 font-bold">
                  <FiCheckCircle className="text-green-500" /> Số tự nhiên{" "}
                  <code>[0;9]</code>, Dấu trừ (<code>-</code>), Dấu phẩy (
                  <code>,</code>)
                </p>
                {answers[q.question_id] &&
                  answers[q.question_id].trim() !== "" &&
                  !isTrackDisabled && (
                    <button
                      onClick={() => handleClearAnswer(q.question_id)}
                      className="text-xs font-bold text-red-500 hover:text-red-700 flex items-center gap-1"
                    >
                      <FiTrash />
                      Xóa
                    </button>
                  )}
              </div>
            </div>
          )}

          {q.type === "essay" && (
            <div className="pl-0 md:pl-8 relative">
              <textarea
                className="input-field p-4 pb-8 text-base min-h-[200px] shadow-sm resize-y"
                placeholder="Nhập bài làm tự luận..."
                value={answers[q.question_id] || ""}
                onChange={(e) =>
                  handleAnswerChange(q.question_id, e.target.value)
                }
                disabled={isTrackDisabled}
                maxLength={q.max_chars ? q.max_chars : undefined}
              />
              {(q.max_words || q.max_chars) && (
                <div
                  className={`absolute bottom-2 right-3 p-1 px-2 text-[10px] font-bold rounded ${q.max_words && countWords(answers[q.question_id] || "") >= q.max_words ? "text-red-600 bg-red-50 border border-red-200" : q.max_chars && (answers[q.question_id] || "").length >= q.max_chars ? "text-red-600 bg-red-50 border border-red-200" : "text-slate-400 bg-slate-50 border border-slate-200"}`}
                >
                  {q.max_words
                    ? `${countWords(answers[q.question_id] || "")}/${q.max_words} từ`
                    : ""}
                  {q.max_chars && !q.max_words
                    ? `${(answers[q.question_id] || "").length}/${q.max_chars} ký tự`
                    : ""}
                </div>
              )}
            </div>
          )}
        </div>,
      );
    });
    return elements;
  };

  if (!paper)
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center font-bold text-base text-slate-500">
        Đang tải phòng thi...
      </div>
    );

  if (result) {
    return (
      <div className="fixed inset-0 z-[9999] bg-slate-50 flex items-center justify-center p-4">
        <div className="content-box max-w-md w-full p-8 text-center shadow-xl">
          <div className="w-16 h-16 bg-green-50 border border-green-200 rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm">
            <svg
              className="w-8 h-8 text-green-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2.5"
                d="M5 13l4 4L19 7"
              ></path>
            </svg>
          </div>
          <h1 className="text-2xl font-black text-slate-900 mb-1">
            Hoàn Thành Bài Thi
          </h1>
          <p className="text-xs text-slate-500 font-bold mb-6">
            Môn thi:{" "}
            <strong className="text-slate-800 uppercase">
              {paper.subject_name}
            </strong>
          </p>
          <div className="bg-blue-50/40 border border-blue-200 p-4 rounded-lg mb-6 shadow-sm">
            {result.auto_scored ? (
              <>
                <p className="text-xs text-blue-900 uppercase font-black tracking-wide mb-1">
                  Điểm Trắc Nghiệm
                </p>
                <p className="text-5xl font-black text-blue-700 my-2">
                  {result.score_info?.mc_score}
                </p>
                <div className="bg-white p-2 px-3 w-fit mx-auto rounded-md shadow-2xs border border-slate-200 mt-3">
                  <p className="text-xs font-bold text-slate-700">
                    Đúng: {result.score_info?.correct_count} /{" "}
                    {paper.total_questions}
                  </p>
                </div>
              </>
            ) : (
              <p className="text-sm font-bold text-blue-900">
                Bài tự luận đang chờ chấm điểm.
              </p>
            )}{" "}
            {result.requires_manual_grading && (
              <p className="mt-3 text-xs font-bold text-amber-800 bg-amber-50 border border-amber-200 p-2 rounded-lg shadow-2xs">
                Có phần Tự luận cần chấm thủ công.
              </p>
            )}
          </div>
          <button
            onClick={() => navigate("/student/dashboard")}
            className="btn-primary w-full py-2.5 text-sm"
          >
            Về Trang Chủ
          </button>
        </div>
      </div>
    );
  }

  const sidebarParts = Array.from(
    new Set(paper.questions.map((q: any) => q.mappedPart || q.part || "part1")),
  );

  return (
    <div className="fixed inset-0 z-[9999] bg-slate-50 flex flex-col overflow-hidden">
      <div className="bg-white p-4 border-b border-slate-200 h-16 flex items-center justify-between shadow-2xs z-30 shrink-0">
        <div className="flex items-center gap-3 w-1/3">
          <button
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className="p-2 rounded hover:bg-slate-50 transition-all text-slate-700 border border-slate-200"
            title={isSidebarCollapsed ? "Mở danh mục" : "Thu gọn"}
          >
            {isSidebarCollapsed ? (
              <FiMaximize2 size={16} />
            ) : (
              <FiMinimize2 size={16} />
            )}
          </button>
          <div className="hidden md:block">
            <h1 className="font-bold text-slate-900 uppercase tracking-wide text-sm">
              {paper.subject_name}
            </h1>
            <p className="text-[10px] text-slate-400 font-medium truncate">
              Mã đề: {paper.paper_code}
            </p>
          </div>
        </div>
        <div className="flex flex-col items-center justify-center w-1/3">
          <p className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-0.5">
            Thời gian
          </p>
          <div
            className={`text-2xl font-mono font-bold tracking-tight ${timeLeft < 300 ? "text-red-600 animate-pulse" : "text-blue-950"}`}
          >
            {formatTime(timeLeft)}
          </div>
        </div>
        <div className="flex justify-end w-1/3">
          <button
            onClick={handleManualSubmit}
            disabled={isSubmitting}
            className="btn-danger px-4 py-2 text-xs font-bold shadow-sm"
          >
            {isSubmitting ? "ĐANG XỬ LÝ" : "NỘP BÀI"}
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden relative">
        {/* Tối ưu hóa vùng Sidebar điều hướng: Sử dụng nền trắng thanh lịch, gỡ bỏ content-box thừa thãi */}
        <div
          className={`bg-white border-r border-slate-200 flex flex-col z-20 transition-all duration-300 shrink-0 shadow-2xs ${isSidebarCollapsed ? "w-0 opacity-0 overflow-hidden border-none" : "w-full md:w-72"}`}
        >
          <div className="p-4 overflow-y-auto flex-1 space-y-6">
            {sidebarParts.map((partKey: any) => {
              const partQs = paper.questions.filter(
                (q: any) => (q.mappedPart || q.part || "part1") === partKey,
              );
              return (
                <div key={`sidebar-${partKey}`} className="space-y-2.5">
                  {/* Phân cách tiêu đề phần tinh gọn, cắt dòng gọn gàng, tránh vỡ đường kẻ */}
                  <div className="border-b border-slate-100 pb-1.5">
                    <span
                      className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block truncate"
                      title={getPartLabel(paper.subject_name, partKey)}
                    >
                      {getPartLabel(paper.subject_name, partKey)}
                    </span>
                  </div>

                  {/* Lưới nút bấm chuẩn mực sử dụng class tiện ích thuần túy, phẳng, thẳng tắp */}
                  <div className="grid grid-cols-5 gap-2">
                    {partQs.map((q: any) => {
                      const isAnswered =
                        q.type === "true_false"
                          ? answers[q.question_id] &&
                            Object.keys(answers[q.question_id]).length > 0
                          : answers[q.question_id] !== undefined &&
                            answers[q.question_id] !== null &&
                            answers[q.question_id].toString().trim() !== "";
                      const isFullyAnswered =
                        q.type === "true_false"
                          ? answers[q.question_id] &&
                            Object.keys(answers[q.question_id]).length === 4
                          : answers[q.question_id] !== undefined &&
                            answers[q.question_id] !== null &&
                            answers[q.question_id].toString().trim() !== "";
                      const safeTrack = q.informatics_track || "common";
                      const isTrackDisabled =
                        safeTrack !== "common" &&
                        selectedTrack !== null &&
                        selectedTrack !== safeTrack;
                      return (
                        <button
                          key={q.question_id}
                          onClick={() =>
                            document
                              .getElementById(`question-${q.question_id}`)
                              ?.scrollIntoView({
                                behavior: "smooth",
                                block: "start",
                              })
                          }
                          className={`w-full aspect-square rounded-md font-bold text-xs flex items-center justify-center transition-all border box-border ${
                            isTrackDisabled
                              ? "bg-slate-50 text-slate-300 border-dashed border-slate-200 cursor-not-allowed"
                              : isAnswered
                                ? isFullyAnswered
                                  ? "bg-blue-600 text-white border-blue-700 font-black shadow-2xs"
                                  : "bg-orange-600 text-white border-orange-700 font-black shadow-2xs"
                                : "bg-white text-slate-700 border-slate-200 hover:border-blue-400 hover:bg-slate-50 shadow-2xs"
                          }`}
                          title={`Câu ${q.question_number}`}
                        >
                          {q.question_number}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 sm:p-6 md:p-8 scroll-smooth bg-slate-50">
          <div className="max-w-5xl mx-auto pb-40">
            <div className="content-box md:hidden text-center mb-5 p-4 shadow-sm">
              <h2 className="text-base font-bold text-slate-900 uppercase">
                {paper.subject_name}
              </h2>
              <span className="bg-slate-50 text-slate-600 px-2.5 py-1 rounded-md border border-slate-200 text-xs font-bold mt-1.5 inline-block">
                Mã đề:{" "}
                <strong className="text-slate-900">{paper.paper_code}</strong>
              </span>
            </div>
            {paper.reading_material && (
              <div className="content-box bg-yellow-50 p-5 border-yellow-200 shadow-sm mb-6">
                <h3 className="text-xs font-bold text-yellow-800 uppercase tracking-wider mb-2">
                  Ngữ liệu chung:
                </h3>
                <MarkdownContent content={paper.reading_material} />
              </div>
            )}
            {renderExamContent()}
          </div>
        </div>
      </div>
    </div>
  );
}
