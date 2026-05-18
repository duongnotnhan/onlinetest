import React, { useEffect, useMemo, useState, memo, useRef } from "react";
import toast from "react-hot-toast";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import remarkGfm from "remark-gfm";
import rehypeKatex from "rehype-katex";
import rehypeRaw from "rehype-raw";
import "katex/dist/katex.min.css";
import { adminAPI, examAPI, uploadAPI, exportAPI } from "@/api";
import {
  FiArrowLeft,
  FiCheckCircle,
  FiFileText,
  FiImage,
  FiPlus,
  FiShuffle,
  FiEdit,
  FiTrash2,
  FiXCircle,
  FiEye,
  FiUpload,
  FiMenu,
  FiDownload,
} from "react-icons/fi";

interface Session {
  exam_session_id: number;
  session_name: string;
  session_type: string;
  start_date: string;
  end_date: string;
  is_published: boolean;
}
interface Subject {
  subject_id: number;
  subject_code: string;
  subject_name: string;
  duration_minutes: number;
}
interface Schedule {
  schedule_id: number;
  session_name: string;
  subject_name: string;
  exam_date: string;
  start_time: string;
  end_time: string;
}
interface Paper {
  paper_id: number;
  paper_code: string;
  session_name: string;
  subject_id: number;
  subject_name: string;
  total_questions: number;
  versions: number;
  is_finalized: boolean;
}
interface Subsection {
  subsection_id: number;
  title?: string;
  content?: string;
  type:
    | "reading_fill_in"
    | "reading_comprehension"
    | "arrangement_correction"
    | "normal";
  shuffle_questions: boolean;
  shuffle_choices: boolean;
  shuffle_items: boolean;
  part: string;
}
interface Question {
  question_id: number;
  question_number: number;
  part: string;
  subsection_id?: number;
  type: string;
  text: string;
  points: number;
  answer_key?: string;
  shuffle_enabled?: boolean;
  choices?: any[];
  items?: any[];
  max_words?: number;
  max_chars?: number;
  informatics_track?: string;
}
interface PaperDetail extends Paper {
  total_points: number;
  versions_count: number;
  reading_material?: string;
  questions: Question[];
  subsections?: Subsection[];
}

function structureForSubject(subjectName?: string, subjectCode?: string) {
  const name = (subjectName || "").toLowerCase();
  const code = (subjectCode || "").toUpperCase();

  if (code === "TOAN" || name.includes("toán")) {
    return [
      {
        key: "part1",
        label: "Phần I. Câu trắc nghiệm nhiều phương án lựa chọn",
        type: "multiple_choice",
        expected: 24,
        points: "0.25đ/câu",
        shuffle: true,
      },
      {
        key: "part2",
        label: "Phần II. Câu trắc nghiệm đúng sai",
        type: "true_false",
        expected: 4,
        points: "0.1-1.0đ/câu",
        shuffle: true,
      },
      {
        key: "part3",
        label: "Phần III. Câu trắc nghiệm trả lời ngắn",
        type: "short_answer",
        expected: 6,
        points: "0.5đ/câu",
        shuffle: true,
      },
    ];
  }

  if (code === "NVVAN" || name.includes("ngữ văn")) {
    return [
      {
        key: "part1",
        label: "Phần I. Đọc Hiểu",
        type: "essay",
        expected: 5,
        points: "4.0đ",
        shuffle: false,
      },
      {
        key: "part2",
        label: "Phần II. Viết",
        type: "essay",
        expected: 2,
        points: "6.0đ",
        shuffle: false,
      },
    ];
  }

  if (code === "TIN_HO" || name.includes("tin học")) {
    return [
      {
        key: "part1",
        label: "Phần I - Câu trắc nghiệm nhiều phương án lựa chọn",
        type: "multiple_choice",
        expected: 24,
        points: "0.25đ/câu",
        shuffle: true,
      },
      {
        key: "part2",
        label: "Phần II - Câu trắc nghiệm đúng sai",
        type: "true_false",
        expected: 6,
        points: "0.1-1.0đ/câu",
        shuffle: false,
      },
    ];
  }

  if (code === "NGA_AN" || name.includes("tiếng anh")) {
    return [
      {
        key: "rc1",
        label: "Reading Comprehension 1",
        type: "multiple_choice",
        expected: 8,
        points: "0.25đ/câu",
        shuffle: true,
        defaultSubType: "reading_comprehension",
      },
      {
        key: "rc2",
        label: "Reading Comprehension 2",
        type: "multiple_choice",
        expected: 10,
        points: "0.25đ/câu",
        shuffle: true,
        defaultSubType: "reading_comprehension",
      },
      {
        key: "rf1",
        label: "Reading Fill in the Blank 1",
        type: "multiple_choice",
        expected: 6,
        points: "0.25đ/câu",
        shuffle: true,
        defaultSubType: "reading_fill_in",
      },
      {
        key: "rf2",
        label: "Reading Fill in the Blank 2",
        type: "multiple_choice",
        expected: 6,
        points: "0.25đ/câu",
        shuffle: true,
        defaultSubType: "reading_fill_in",
      },
      {
        key: "rf3",
        label: "Reading Fill in the Blank 3",
        type: "multiple_choice",
        expected: 5,
        points: "0.25đ/câu",
        shuffle: true,
        defaultSubType: "reading_fill_in",
      },
      {
        key: "rs",
        label: "Reordering Sentences",
        type: "multiple_choice",
        expected: 5,
        points: "0.25đ/câu",
        shuffle: true,
        defaultSubType: "arrangement_correction",
      },
    ];
  }

  if (name.includes("tiếng") || name.includes("ngoại ngữ")) {
    return [
      {
        key: "part1",
        label: "Phần I - Câu trắc nghiệm Ngoại Ngữ",
        type: "multiple_choice",
        expected: 40,
        points: "0.25đ/câu",
        shuffle: true,
      },
    ];
  }

  return [
    {
      key: "part1",
      label: "Phần I. Câu trắc nghiệm nhiều phương án lựa chọn",
      type: "multiple_choice",
      expected: 18,
      points: "0.25đ/câu",
      shuffle: true,
    },
    {
      key: "part2",
      label: "Phần II. Câu trắc nghiệm đúng sai",
      type: "true_false",
      expected: 4,
      points: "0.1-1.0đ/câu",
      shuffle: true,
    },
    {
      key: "part3",
      label: "Phần III. Câu trắc nghiệm trả lời ngắn",
      type: "short_answer",
      expected: 6,
      points: "0.25đ/câu",
      shuffle: true,
    },
  ];
}

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
  const processedContent = content.replace(
    /<code>([\s\S]*?)<\/code>/g,
    (codeInside) => {
      const escapedCode = codeInside
        .replace(/^\s+|\s+$/g, "")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
      return `<code>${escapedCode}</code>`;
    },
  );

  return (
    <div className="prose max-w-none text-gray-900 text-base leading-relaxed custom-markdown-table">
      <ReactMarkdown
        remarkPlugins={[
          [remarkGfm, { singleTilde: false, autolink: false }],
          remarkMath,
        ]}
        rehypePlugins={[rehypeRaw, rehypeKatex]}
      >
        {processedContent}
      </ReactMarkdown>
    </div>
  );
});

function MarkdownBox({
  label,
  value,
  onChange,
  minHeight = "min-h-[120px]",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  minHeight?: string;
}) {
  const [uploading, setUploading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const attachImage = async (file?: File) => {
    if (!file) return;
    setUploading(true);
    try {
      const response = await uploadAPI.uploadImage(file);
      insertAtCursor(`\n\n![${file.name}](${response.data.url})\n`);
      toast.success("Đính kèm ảnh thành công");
    } catch (error) {
      toast.error("Lỗi tải ảnh: " + (error as Error).message);
    } finally {
      setUploading(false);
    }
  };

  const insertAtCursor = (prefix: string, suffix?: string) => {
    if (!textareaRef.current) {
      onChange(`${value}${prefix}`);
      return;
    }
    const start = textareaRef.current.selectionStart;
    const end = textareaRef.current.selectionEnd;
    if (suffix !== undefined) {
      const selectedText = value.substring(start, end) || "Nội dung";
      const replacement = `${prefix}${selectedText}${suffix}`;
      onChange(value.substring(0, start) + replacement + value.substring(end));
    } else {
      onChange(value.substring(0, start) + prefix + value.substring(end));
    }
    setTimeout(() => textareaRef.current?.focus(), 0);
  };

  const applyAlignment = (align: string) => {
    insertAtCursor(`<div style="text-align: ${align};">\n\n`, `\n\n</div>`);
  };

  return (
    <div className="space-y-2">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 pb-2">
        <label className="text-sm font-bold text-gray-800">{label}</label>
        <div className="flex flex-wrap items-center gap-1 bg-gray-50 p-1 rounded-lg border border-gray-200">
          <button
            type="button"
            onClick={() => insertAtCursor("**", "**")}
            className="px-2.5 py-1 bg-white hover:bg-gray-100 text-gray-800 rounded font-bold text-xs transition-all shadow-2xs"
            title="In đậm"
          >
            B
          </button>
          <button
            type="button"
            onClick={() => insertAtCursor("*", "*")}
            className="px-2.5 py-1 bg-white hover:bg-gray-100 text-gray-800 rounded italic text-xs transition-all font-serif shadow-2xs"
            title="In nghiêng"
          >
            I
          </button>
          <button
            type="button"
            onClick={() => insertAtCursor("<u>", "</u>")}
            className="px-2.5 py-1 bg-white hover:bg-gray-100 text-gray-800 rounded underline text-xs transition-all font-medium shadow-2xs"
            title="Gạch chân"
          >
            U
          </button>
          <span className="w-px h-3 bg-gray-300 mx-1"></span>
          <button
            type="button"
            onClick={() => applyAlignment("left")}
            className="px-2.5 py-1 bg-white hover:bg-gray-100 text-gray-800 rounded font-medium text-xs transition-all shadow-2xs"
            title="Căn trái"
          >
            Trái
          </button>
          <button
            type="button"
            onClick={() => applyAlignment("center")}
            className="px-2.5 py-1 bg-white hover:bg-gray-100 text-gray-800 rounded font-medium text-xs transition-all shadow-2xs"
            title="Căn giữa"
          >
            Giữa
          </button>
          <button
            type="button"
            onClick={() => applyAlignment("right")}
            className="px-2.5 py-1 bg-white hover:bg-gray-100 text-gray-800 rounded font-medium text-xs transition-all shadow-2xs"
            title="Căn phải"
          >
            Phải
          </button>
          <button
            type="button"
            onClick={() => applyAlignment("justify")}
            className="px-2.5 py-1 bg-white hover:bg-gray-100 text-gray-800 rounded font-medium text-xs transition-all shadow-2xs"
            title="Căn đều"
          >
            Đều
          </button>
          <span className="w-px h-3 bg-gray-300 mx-1"></span>
          <button
            type="button"
            onClick={() =>
              insertAtCursor(
                "\n\n| Cột 1 | Cột 2 | Cột 3 |\n|---|---|---|\n| Dữ liệu | Dữ liệu | Dữ liệu |\n| Dữ liệu | Dữ liệu | Dữ liệu |\n\n",
              )
            }
            className="px-2.5 py-1 bg-white hover:bg-gray-100 text-gray-800 rounded font-medium text-xs transition-all shadow-2xs"
            title="Chèn bảng"
          >
            Bảng
          </button>
          <span className="w-px h-3 bg-gray-300 mx-1"></span>
          <label
            className={`px-2.5 py-1 bg-white hover:bg-gray-100 text-blue-600 rounded font-medium text-xs transition-all shadow-2xs flex items-center gap-1.5 cursor-pointer ${uploading ? "opacity-50 pointer-events-none" : ""}`}
          >
            <FiImage /> {uploading ? "..." : "Ảnh"}
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => attachImage(e.target.files?.[0])}
            />
          </label>
        </div>
      </div>
      <textarea
        ref={textareaRef}
        className={`input-field font-mono text-base ${minHeight} p-3.5 leading-relaxed`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Hỗ trợ gõ cú pháp Markdown thuần túy, công thức toán học $x^2$, chèn bảng biểu..."
      />
      <div className="mt-3 bg-gray-50 p-4 rounded-lg border border-gray-200 min-h-[80px]">
        <p className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-2 border-b border-gray-200 pb-1">
          Bản xem trước hiển thị:
        </p>
        <MarkdownContent content={value} />
      </div>
    </div>
  );
}

export default function ExamsPage() {
  const [activeTab, setActiveTab] = useState<"sessions" | "papers">("sessions");
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [loading, setLoading] = useState(true);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState("");
  const [,setSelectedPaperId] = useState<number | null>(null);
  const [paperDetail, setPaperDetail] = useState<PaperDetail | null>(null);

  const [sessionForm, setSessionForm] = useState({
    session_name: "",
    session_type: "official",
    start_date: "",
    end_date: "",
    description: "",
  });
  const [scheduleForm, setScheduleForm] = useState({
    exam_session_id: "",
    subject_id: "",
    exam_date: "",
    start_time: "",
    end_time: "",
  });
  const [paperForm, setPaperForm] = useState({
    exam_session_id: "",
    subject_id: "",
    paper_code: "",
    randomization_enabled: true,
  });

  const [showQuestionModal, setShowQuestionModal] = useState(false);
  const [isEditingQuestion, setIsEditingQuestion] = useState(false);
  const [editingQuestionId, setEditingQuestionId] = useState<number | null>(
    null,
  );
  const [questionForm, setQuestionForm] = useState<any>({
    part: "part1",
    question_type: "multiple_choice",
    question_text: "",
    points: "0.25",
    correct_answer: "",
    subsection_id: "",
    informatics_track: "",
    max_words: "",
    max_chars: "",
  });
  const [choiceDrafts, setChoiceDrafts] = useState(["", "", "", ""]);
  const [trueFalseDrafts, setTrueFalseDrafts] = useState([
    { text: "", correct_value: "true" },
    { text: "", correct_value: "true" },
    { text: "", correct_value: "true" },
    { text: "", correct_value: "true" },
  ]);
  const [shortAnswerCells, setShortAnswerCells] = useState(["", "", "", ""]);

  const [showSubsectionModal, setShowSubsectionModal] = useState(false);
  const [isEditingSubsection, setIsEditingSubsection] = useState(false);
  const [editingSubsectionId, setEditingSubsectionId] = useState<number | null>(
    null,
  );
  const [subsectionForm, setSubsectionForm] = useState<any>({
    title: "",
    content: "",
    type: "normal",
    shuffle_questions: true,
    shuffle_choices: true,
    shuffle_items: true,
    part: "part1",
  });
  const [editingReadingMaterial, setEditingReadingMaterial] = useState(false);
  const [tempReadingMaterial, setTempReadingMaterial] = useState("");

  const [showImportModal, setShowImportModal] = useState(false);
  const [importForm, setImportForm] = useState({
    part: "part1",
    questionType: "multiple_choice",
  });
  const [importFile, setImportFile] = useState<File | null>(null);
  const [isImporting, setIsImporting] = useState(false);

  const dragItem = useRef<number | null>(null);
  const dragOverItem = useRef<number | null>(null);
  const dragChildItem = useRef<number | null>(null);
  const dragOverChildItem = useRef<number | null>(null);

  const subjectsData = useMemo(() => subjects, [subjects]);
  const selectedSubject = useMemo(
    () =>
      subjects.find((s) => s.subject_id === Number(scheduleForm.subject_id)),
    [subjects, scheduleForm.subject_id],
  );
  const paperSubject = useMemo(
    () =>
      subjectsData.find((s) => s.subject_name === paperDetail?.subject_name),
    [subjectsData, paperDetail],
  );
  const paperStructure = useMemo(
    () =>
      structureForSubject(
        paperDetail?.subject_name,
        paperSubject?.subject_code,
      ),
    [paperDetail, paperSubject],
  );

  const fetchData = async () => {
    try {
      const [se, su, sc, pa] = await Promise.all([
        adminAPI.getExamSessions(),
        adminAPI.getSubjects(),
        adminAPI.getExamSchedules(
          selectedSessionId ? Number(selectedSessionId) : undefined,
        ),
        examAPI.getPapers(
          selectedSessionId ? Number(selectedSessionId) : undefined,
        ),
      ]);
      setSessions(se.data.data || []);
      setSubjects(su.data.data || []);
      setSchedules(sc.data.data || []);
      setPapers(pa.data.data || []);
    } catch (e) {
      toast.error("Lỗi tải dữ liệu hệ thống: " + (e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedSessionId]);

  const loadPaperDetail = async (id: number) => {
    try {
      const res = await examAPI.getPaperDetail(id);
      setPaperDetail(res.data);
      setSelectedPaperId(id);
    } catch (e) {
      toast.error("Lỗi tải chi tiết đề thi: " + (e as Error).message);
    }
  };

  const handleGenerateVersions = async () => {
    if (!paperDetail) return;
    const numStr = prompt(
      "Nhập số lượng đề hoán vị cần sinh tự động (tối đa 20):",
      "8",
    );
    if (!numStr) return;
    const num = parseInt(numStr, 20);
    if (isNaN(num) || num < 1 || num > 20)
      return toast.error("Số lượng nhập vào không hợp lệ");
    try {
      await examAPI.generateVersions(paperDetail.paper_id, num);
      toast.success(`Đã tự động xáo trộn và sinh ${num} mã đề!`);
      loadPaperDetail(paperDetail.paper_id);
    } catch (err: any) {
      toast.error(err.response?.data?.error || "Lỗi phát sinh hoán vị");
    }
  };

  const handleSaveQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!paperDetail) return;

    let actualPart = questionForm.part;
    if (["rc1", "rc2", "rf1", "rf2", "rf3", "rs"].includes(actualPart)) {
      // Giữ nguyên các định danh chuyên sâu bộ môn Tiếng Anh
    } else if (
      actualPart === "part1" &&
      paperDetail.subject_name === "Ngữ Văn"
    ) {
      actualPart = "reading";
    } else if (
      actualPart === "part2" &&
      paperDetail.subject_name === "Ngữ Văn"
    ) {
      actualPart = "writing";
    }

    const mappedChoices = ["A", "B", "C", "D"].map((l, i) => ({
      choice_label: l,
      label: l,
      choice_text: choiceDrafts[i] || "",
      text: choiceDrafts[i] || "",
      content: choiceDrafts[i] || "",
      display_order: i + 1,
    }));

    const payload: any = {
      ...questionForm,
      part: actualPart,
      question_text: questionForm.question_text,
      text: questionForm.question_text,
      correct_answer: questionForm.correct_answer,
      answer_key: questionForm.correct_answer,
      answer_value: questionForm.correct_answer,
      answer: questionForm.correct_answer,
      points: Number(questionForm.points),
      max_words: questionForm.max_words ? Number(questionForm.max_words) : null,
      max_chars: questionForm.max_chars ? Number(questionForm.max_chars) : null,
      subsection_id: questionForm.subsection_id
        ? Number(questionForm.subsection_id)
        : null,
      section_id: questionForm.subsection_id
        ? Number(questionForm.subsection_id)
        : null,
      informatics_track:
        questionForm.informatics_track === ""
          ? null
          : questionForm.informatics_track,
    };

    if (questionForm.question_type === "multiple_choice") {
      payload.choices = mappedChoices;
      payload.options = mappedChoices;
    }
    if (questionForm.question_type === "true_false") {
      payload.items = ["a", "b", "c", "d"].map((l, i) => ({
        item_label: l,
        label: l,
        item_text: trueFalseDrafts[i].text,
        text: trueFalseDrafts[i].text,
        correct_value: trueFalseDrafts[i].correct_value,
        display_order: i + 1,
      }));
    }
    if (questionForm.question_type === "short_answer") {
      const chot = shortAnswerCells.join("").trim();
      payload.correct_answer = chot;
      payload.answer_key = chot;
      payload.answer_value = chot;
      payload.answer = chot;
    }

    try {
      if (isEditingQuestion && editingQuestionId) {
        await examAPI.updateQuestion(editingQuestionId, payload);
      } else {
        await examAPI.addQuestion(paperDetail.paper_id, payload);
      }
      toast.success("Lưu cấu hình câu hỏi thành công");
      setShowQuestionModal(false);
      loadPaperDetail(paperDetail.paper_id);
    } catch (err: any) {
      toast.error(err.response?.data?.error || "Lỗi cập nhật hệ thống");
    }
  };

  const handleSaveSubsection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!paperDetail) return;
    let actualPart = subsectionForm.part;
    if (actualPart === "part1" && paperDetail.subject_name === "Ngữ Văn")
      actualPart = "reading";
    if (actualPart === "part2" && paperDetail.subject_name === "Ngữ Văn")
      actualPart = "writing";

    const payload = { ...subsectionForm, part: actualPart };
    try {
      if (isEditingSubsection && editingSubsectionId)
        await examAPI.updateSubsection(editingSubsectionId, payload);
      else await examAPI.addSubsection(paperDetail.paper_id, payload);
      toast.success("Cập nhật vùng ngữ liệu thành công");
      setShowSubsectionModal(false);
      loadPaperDetail(paperDetail.paper_id);
    } catch (err) {
      toast.error("Lỗi lưu phân vùng: " + (err as Error).message);
    }
  };

  const openImportModal = (partKey: string) => {
    setImportForm({ part: partKey, questionType: "multiple_choice" });
    setImportFile(null);
    setShowImportModal(true);
  };

  const handleImportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importFile || !paperDetail) return;
    setIsImporting(true);
    try {
      const res = await examAPI.importQuestionsCsv(
        paperDetail.paper_id,
        importForm.part,
        importForm.questionType,
        importFile,
      );
      toast.success(`Nạp tự động thành công ${res.data.imported} câu hỏi!`);
      setShowImportModal(false);
      loadPaperDetail(paperDetail.paper_id);
    } catch (error: any) {
      toast.error(error.response?.data?.error || "Lỗi phân tích cú pháp");
    } finally {
      setIsImporting(false);
    }
  };

  const getCsvFormatGuide = () => {
    if (importForm.questionType === "multiple_choice")
      return "Header: NoiDung | Diem | A | B | C | D | DapAnDung | DinhHuong";
    if (importForm.questionType === "true_false")
      return "Header: NoiDung | Diem | Y_a | DS_a | Y_b | DS_b | Y_c | DS_c | Y_d | DS_d | DinhHuong";
    return "Header: NoiDung | Diem | DapAn | DinhHuong";
  };

  const handleSort = async (partKey: string) => {
    if (
      dragItem.current === null ||
      dragOverItem.current === null ||
      !paperDetail
    )
      return;
    const questionsList = paperDetail.questions || [];
    const subsectionsList = paperDetail.subsections || [];
    const mappedQuestions = questionsList.map((q) => ({
      ...q,
      mappedPart:
        q.part === "reading"
          ? "part1"
          : q.part === "writing"
            ? "part2"
            : q.part,
    }));
    const blocks: any[] = [];
    subsectionsList
      .filter(
        (s) =>
          (s.part === "reading"
            ? "part1"
            : s.part === "writing"
              ? "part2"
              : s.part) === partKey,
      )
      .forEach((sub) => {
        const subQs = mappedQuestions.filter(
          (q) => String(q.subsection_id) === String(sub.subsection_id),
        );
        const minQ =
          subQs.length > 0
            ? Math.min(...subQs.map((q) => q.question_number))
            : 9999;
        blocks.push({
          type: "subsection",
          data: sub,
          questions: subQs,
          order: minQ,
        });
      });
    mappedQuestions
      .filter((q) => q.mappedPart === partKey && !q.subsection_id)
      .forEach((q) => {
        blocks.push({
          type: "loose",
          data: q,
          questions: [q],
          order: q.question_number,
        });
      });

    blocks.sort((a, b) => a.order - b.order);
    const draggedBlock = blocks[dragItem.current];
    blocks.splice(dragItem.current, 1);
    blocks.splice(dragOverItem.current, 0, draggedBlock);

    const finalOrderedQuestionIds: number[] = [];
    paperStructure.forEach((part) => {
      if (part.key === partKey) {
        blocks.forEach((b) => {
          const sortedQs = [...b.questions].sort(
            (a, b) => a.question_number - b.question_number,
          );
          sortedQs.forEach((q) => finalOrderedQuestionIds.push(q.question_id));
        });
      } else {
        const otherBlocks: any[] = [];
        subsectionsList
          .filter(
            (s) =>
              (s.part === "reading"
                ? "part1"
                : s.part === "writing"
                  ? "part2"
                  : s.part) === part.key,
          )
          .forEach((sub) => {
            const subQs = mappedQuestions.filter(
              (q) => String(q.subsection_id) === String(sub.subsection_id),
            );
            const minQ =
              subQs.length > 0
                ? Math.min(...subQs.map((q) => q.question_number))
                : 9999;
            otherBlocks.push({
              type: "subsection",
              data: sub,
              questions: subQs,
              order: minQ,
            });
          });
        mappedQuestions
          .filter((q) => q.mappedPart === part.key && !q.subsection_id)
          .forEach((q) => {
            otherBlocks.push({
              type: "loose",
              data: q,
              questions: [q],
              order: q.question_number,
            });
          });
        otherBlocks.sort((a, b) => a.order - b.order);
        otherBlocks.forEach((b) => {
          const sortedQs = [...b.questions].sort(
            (a, b) => a.question_number - b.question_number,
          );
          sortedQs.forEach((q) => finalOrderedQuestionIds.push(q.question_id));
        });
      }
    });
    dragItem.current = null;
    dragOverItem.current = null;
    try {
      await examAPI.reorderQuestions(
        paperDetail.paper_id,
        finalOrderedQuestionIds,
      );
      toast.success("Đã tự động chốt lại trật tự toàn bài");
      loadPaperDetail(paperDetail.paper_id);
    } catch (e) {
      toast.error("Lỗi đồng bộ thứ tự: " + (e as Error).message);
    }
  };

  const handleSortChild = async (subsectionId: number) => {
    if (
      dragChildItem.current === null ||
      dragOverChildItem.current === null ||
      !paperDetail
    )
      return;
    const questionsList = paperDetail.questions || [];
    const subsectionsList = paperDetail.subsections || [];
    const targetSubQs = questionsList
      .filter((q) => String(q.subsection_id) === String(subsectionId))
      .sort((a, b) => a.question_number - b.question_number);
    if (targetSubQs.length < 2) return;

    const draggedQ = targetSubQs[dragChildItem.current];
    targetSubQs.splice(dragChildItem.current, 1);
    targetSubQs.splice(dragOverChildItem.current, 0, draggedQ);

    const mappedQuestions = questionsList.map((q) => ({
      ...q,
      mappedPart:
        q.part === "reading"
          ? "part1"
          : q.part === "writing"
            ? "part2"
            : q.part,
    }));
    const finalOrderedQuestionIds: number[] = [];
    paperStructure.forEach((part) => {
      const partBlocks: any[] = [];
      subsectionsList
        .filter(
          (s) =>
            (s.part === "reading"
              ? "part1"
              : s.part === "writing"
                ? "part2"
                : s.part) === part.key,
        )
        .forEach((sub) => {
          const subQs = mappedQuestions.filter(
            (q) => String(q.subsection_id) === String(sub.subsection_id),
          );
          const minQ =
            subQs.length > 0
              ? Math.min(...subQs.map((q) => q.question_number))
              : 9999;
          partBlocks.push({
            type: "subsection",
            data: sub,
            questions: subQs,
            order: minQ,
          });
        });
      mappedQuestions
        .filter((q) => q.mappedPart === part.key && !q.subsection_id)
        .forEach((q) => {
          partBlocks.push({
            type: "loose",
            data: q,
            questions: [q],
            order: q.question_number,
          });
        });
      partBlocks.sort((a, b) => a.order - b.order);
      partBlocks.forEach((b) => {
        if (
          b.type === "subsection" &&
          String(b.data.subsection_id) === String(subsectionId)
        ) {
          targetSubQs.forEach((q) =>
            finalOrderedQuestionIds.push(q.question_id),
          );
        } else {
          const sortedQs = [...b.questions].sort(
            (a, b) => a.question_number - b.question_number,
          );
          sortedQs.forEach((q) => finalOrderedQuestionIds.push(q.question_id));
        }
      });
    });
    dragChildItem.current = null;
    dragOverChildItem.current = null;
    try {
      await examAPI.reorderQuestions(
        paperDetail.paper_id,
        finalOrderedQuestionIds,
      );
      toast.success("Đã cập nhật lại trật tự câu hỏi trong đoạn");
      loadPaperDetail(paperDetail.paper_id);
    } catch (e) {
      toast.error("Lỗi đồng bộ thứ tự con: " + (e as Error).message);
    }
  };

  const openAddQuestionModal = (partKey: string, subsectionId: string = "") => {
    const partObj = paperStructure.find((p) => p.key === partKey);
    let pts = "0.25";
    if (partKey === "part2" && paperDetail?.subject_name === "Ngữ Văn")
      pts = "6.0";
    if (partKey === "part1" && paperDetail?.subject_name === "Ngữ Văn")
      pts = "1.0";

    setQuestionForm({
      part: partKey,
      question_type: partObj?.type || "multiple_choice",
      question_text: "",
      points: pts,
      correct_answer: "",
      shuffle_enabled: partObj?.shuffle ?? true,
      subsection_id: subsectionId,
      informatics_track: "",
      max_words: "",
      max_chars: "",
    });
    setChoiceDrafts(["", "", "", ""]);
    setShortAnswerCells(["", "", "", ""]);
    setTrueFalseDrafts([
      { text: "", correct_value: "true" },
      { text: "", correct_value: "true" },
      { text: "", correct_value: "true" },
      { text: "", correct_value: "true" },
    ]);
    setIsEditingQuestion(false);
    setShowQuestionModal(true);
  };

  const openAddSubsectionModal = (
    partKey: string,
    customTitle: string = "",
    defaultTypeText: string = "normal",
  ) => {
    const isEnglish =
      paperDetail?.subject_name.toLowerCase().includes("tiếng anh") ||
      paperDetail?.subject_name.toLowerCase().includes("ngoại ngữ");
    setSubsectionForm({
      title: customTitle || "",
      content: "",
      type: defaultTypeText,
      shuffle_questions: !isEnglish,
      shuffle_choices: true,
      shuffle_items: true,
      part: partKey,
    });
    setIsEditingSubsection(false);
    setShowSubsectionModal(true);
  };

  const openEditModal = (q: any) => {
    const resolvedPart = q.mappedPart || q.part || "part1";
    setQuestionForm({
      part: resolvedPart,
      question_type: q.type || "multiple_choice",
      question_text: q.text || "",
      points: q.points ? String(q.points) : "0.25",
      correct_answer: q.answer_key || "",
      shuffle_enabled: q.shuffle_enabled ?? true,
      subsection_id: q.subsection_id || "",
      informatics_track: q.informatics_track || "",
      max_words: q.max_words ? String(q.max_words) : "",
      max_chars: q.max_chars ? String(q.max_chars) : "",
    });
    const newChoices = ["", "", "", ""];
    if (q.choices)
      q.choices.forEach((c: any, i: number) => {
        if (i < 4) newChoices[i] = c.choice_text || c.text || c.content || "";
      });
    setChoiceDrafts(newChoices);

    const newTF = [
      { text: "", correct_value: "true" },
      { text: "", correct_value: "true" },
      { text: "", correct_value: "true" },
      { text: "", correct_value: "true" },
    ];
    if (q.items)
      q.items.forEach((it: any, i: number) => {
        if (i < 4) {
          newTF[i].text = it.item_text || it.text || "";
          newTF[i].correct_value = String(it.correct_value);
        }
      });
    setTrueFalseDrafts(newTF);

    if (q.type === "short_answer") {
      const chars = (q.answer_key || "").split("").slice(0, 4);
      setShortAnswerCells([...chars, ...new Array(4 - chars.length).fill("")]);
    } else {
      setShortAnswerCells(["", "", "", ""]);
    }
    setIsEditingQuestion(true);
    setEditingQuestionId(q.question_id);
    setShowQuestionModal(true);
  };

  const deleteQuestion = async (id: number) => {
    if (!confirm("Hệ thống sẽ xóa vĩnh viễn câu hỏi này. Tiếp tục?")) return;
    try {
      await examAPI.deleteQuestion(id);
      toast.success("Đã xóa câu hỏi");
      loadPaperDetail(paperDetail!.paper_id);
    } catch (e) {
      toast.error("Lỗi thao tác xóa: " + (e as Error).message);
    }
  };

  const deleteSubsection = async (id: number) => {
    if (
      !confirm(
        "Xóa phân vùng sẽ giải phóng các câu con ra vùng tự do. Tiếp tục?",
      )
    )
      return;
    try {
      await examAPI.deleteSubsection(id);
      toast.success("Đã gỡ bỏ phân vùng");
      loadPaperDetail(paperDetail!.paper_id);
    } catch (e) {
      toast.error("Lỗi gỡ bỏ phân vùng: " + (e as Error).message);
    }
  };

  const createSession = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await adminAPI.createExamSession(sessionForm);
      toast.success("Khởi tạo kỳ thi thành công");
      setSessionForm({
        session_name: "",
        session_type: "official",
        start_date: "",
        end_date: "",
        description: "",
      });
      fetchData();
    } catch (e) {
      toast.error("Lỗi khởi tạo: " + (e as Error).message);
    }
  };
  const createSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSubject) return;
    const start = new Date(`2000-01-01T${scheduleForm.start_time}:00`);
    const end = new Date(`2000-01-01T${scheduleForm.end_time}:00`);
    if (start >= end)
      return toast.error("Giờ kết thúc phải diễn ra sau giờ bắt đầu");
    try {
      await adminAPI.createExamSchedule({
        ...scheduleForm,
        exam_session_id: Number(scheduleForm.exam_session_id),
        subject_id: Number(scheduleForm.subject_id),
      });
      toast.success("Gán lịch thi thành công");
      fetchData();
    } catch (e: any) {
      toast.error("Lỗi gán lịch: " + (e as Error).message);
    }
  };
  const createPaper = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await examAPI.createPaper(paperForm);
      toast.success("Khởi tạo mã đề gốc thành công");
      setPaperForm({
        exam_session_id: paperForm.exam_session_id,
        subject_id: "",
        paper_code: "",
        randomization_enabled: true,
      });
      fetchData();
      loadPaperDetail(res.data.paper_id);
    } catch (e) {
      toast.error("Lỗi tạo mã đề: " + (e as Error).message);
    }
  };
  const publishSession = async (id: number) => {
    try {
      await adminAPI.publishExamSession(id);
      toast.success("Đã công bố chính thức");
      fetchData();
    } catch (e) {
      toast.error("Lỗi công bố: " + (e as Error).message);
    }
  };

  const renderQuestionBlock = (q: any, showControls = true) => (
    <div
      key={`question-${q.question_id}`}
      className="content-box hover:border-blue-400 transition-all shadow-sm my-3 p-5"
    >
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1 overflow-hidden">
          <div className="font-bold text-base mb-2 text-blue-900 flex items-center gap-2">
            Câu {q.question_number}:
            {q.informatics_track && q.informatics_track !== "common" && (
              <span className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded-md font-bold uppercase tracking-wider">
                {q.informatics_track === "computer_science" ? "CS" : "ICT"}
              </span>
            )}
          </div>
          <MarkdownContent content={q.text} />

          {q.type === "multiple_choice" && q.choices && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4 text-base">
              {q.choices.map((c: any, idx: number) => {
                const choiceLabel =
                  c.choice_label || c.label || ["A", "B", "C", "D"][idx];
                const isChot =
                  q.answer_key &&
                  q.answer_key.toUpperCase() === choiceLabel.toUpperCase();
                return (
                  <div
                    key={`choice-${c.choice_id || idx}`}
                    className={`flex items-start gap-3 p-3 rounded-lg border transition-all ${isChot ? "bg-green-50 border-green-300 text-green-950 font-bold shadow-sm" : "bg-slate-50 border-slate-200"}`}
                  >
                    <span className="font-black mt-0.5 text-slate-800">
                      {choiceLabel}.
                    </span>
                    <div className="flex-1 overflow-hidden">
                      <MarkdownContent
                        content={c.choice_text || c.text || c.content || ""}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
          {q.type === "true_false" && q.items && (
            <div className="mt-4 space-y-3 text-base">
              {q.items.map((it: any, idx: number) => {
                const itemLabel =
                  it.item_label || it.label || ["a", "b", "c", "d"][idx];
                return (
                  <div
                    key={`item-${it.item_id || idx}`}
                    className="flex justify-between items-center bg-slate-50 p-3 rounded-lg border border-slate-200 gap-4"
                  >
                    <div className="flex items-start gap-3 flex-1">
                      <span className="font-black mt-0.5 text-slate-800">
                        {itemLabel})
                      </span>
                      <div className="flex-1 overflow-hidden">
                        <MarkdownContent
                          content={it.item_text || it.text || ""}
                        />
                      </div>
                    </div>
                    <span
                      className={`text-xs px-3 py-1 rounded-md font-bold shrink-0 uppercase tracking-wider shadow-sm ${it.correct_value === "true" ? "bg-green-600 text-white" : "bg-red-600 text-white"}`}
                    >
                      {it.correct_value === "true" ? "Đúng" : "Sai"}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
          {q.type === "short_answer" && (
            <div className="mt-4 text-sm bg-blue-50 border border-blue-100 p-3 rounded-lg flex items-center gap-2">
              <span className="font-bold text-blue-900 uppercase">
                Đáp án chốt:
              </span>{" "}
              <span className="font-mono text-base font-bold text-blue-700">
                {q.answer_key}
              </span>
            </div>
          )}
          {q.type === "essay" && (
            <div className="mt-4 text-sm bg-amber-50 border border-amber-100 p-3 rounded-lg">
              <span className="font-bold text-amber-900 uppercase block mb-1">
                Gợi ý chấm:
              </span>{" "}
              <MarkdownContent
                content={q.answer_key || "Chưa cung cấp hướng dẫn"}
              />
            </div>
          )}
        </div>

        {showControls && (
          <div className="flex gap-1.5 shrink-0 bg-slate-50 p-1.5 rounded-lg border border-slate-200">
            <button
              onClick={() => openEditModal(q)}
              className="text-blue-600 hover:bg-white p-2 rounded transition-colors"
              title="Chỉnh sửa"
            >
              <FiEdit size={16} />
            </button>
            <button
              onClick={() => deleteQuestion(q.question_id)}
              className="text-red-600 hover:bg-white p-2 rounded transition-colors"
              title="Xóa"
            >
              <FiTrash2 size={16} />
            </button>
          </div>
        )}
      </div>
      {showControls && (
        <div className="text-xs text-slate-400 mt-4 pt-3 border-t border-slate-100 flex gap-4 font-medium tracking-wide">
          <span className="capitalize">{q.type.replace("_", " ")}</span> •{" "}
          <span className="text-blue-600 font-bold">{q.points} điểm</span> •{" "}
          <span>{q.shuffle_enabled ? "Đảo tự động" : "Cố định"}</span>
        </div>
      )}
    </div>
  );

  if (loading)
    return (
      <div className="min-h-screen flex items-center justify-center font-bold text-base text-slate-500">
        Đang đồng bộ cơ sở dữ liệu...
      </div>
    );

  if (paperDetail) {
    const questionsList = paperDetail.questions || [];
    const subsectionsList = paperDetail.subsections || [];
    const mappedQuestions = questionsList.map((q) => ({
      ...q,
      mappedPart:
        q.part === "reading"
          ? "part1"
          : q.part === "writing"
            ? "part2"
            : q.part,
    }));

    if (isPreviewMode) {
      return (
        <div className="max-w-5xl mx-auto p-6 md:p-8 bg-white shadow-sm my-8 rounded-xl border border-slate-200">
          <div className="border-b pb-4 mb-6 flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-black text-slate-900">
                XEM TRƯỚC: MÃ ĐỀ {paperDetail.paper_code}
              </h2>
              <p className="text-sm text-slate-500 font-medium mt-1">
                Môn thi: {paperDetail.subject_name}
              </p>
            </div>
            <button
              onClick={() => setIsPreviewMode(false)}
              className="btn-primary text-xs"
            >
              Thoát chế độ xem
            </button>
          </div>

          {paperDetail.reading_material && (
            <div className="mb-6 bg-yellow-50 p-5 rounded-xl border border-yellow-100 shadow-sm">
              <h3 className="text-sm font-bold text-yellow-800 uppercase tracking-wider mb-2">
                Ngữ liệu chung:
              </h3>
              <MarkdownContent content={paperDetail.reading_material} />
            </div>
          )}

          <div className="space-y-8">
            {paperStructure.map((part) => {
              const pBlocks: any[] = [];
              subsectionsList
                .filter(
                  (s) =>
                    (s.part === "reading"
                      ? "part1"
                      : s.part === "writing"
                        ? "part2"
                        : s.part) === part.key,
                )
                .forEach((sub) => {
                  const subQs = mappedQuestions.filter(
                    (q) =>
                      String(q.subsection_id) === String(sub.subsection_id),
                  );
                  const minQ =
                    subQs.length > 0
                      ? Math.min(...subQs.map((q) => q.question_number))
                      : 9999;
                  pBlocks.push({
                    type: "subsection",
                    data: sub,
                    questions: subQs,
                    order: minQ,
                  });
                });

              const looseQs = mappedQuestions.filter(
                (q) => q.mappedPart === part.key && !q.subsection_id,
              );
              looseQs.forEach((q) => {
                pBlocks.push({
                  type: "loose",
                  data: q,
                  questions: [q],
                  order: q.question_number,
                });
              });
              pBlocks.sort((a, b) => a.order - b.order);
              if (pBlocks.length === 0) return null;

              const partInstruction = generateInstructionBanner(
                paperDetail.subject_name,
                looseQs,
                undefined,
              );

              return (
                <div
                  key={`prev-part-${part.key}`}
                  className="space-y-5 pt-6 border-t border-slate-200"
                >
                  <h3 className="font-black text-lg text-blue-900 uppercase tracking-wide">
                    {part.label}
                  </h3>
                  {partInstruction && (
                    <p className="text-sm font-bold text-slate-700 bg-slate-50 p-3 rounded-lg border border-slate-200 shadow-sm">
                      {partInstruction}
                    </p>
                  )}

                  {pBlocks.map((b) => {
                    if (b.type === "subsection") {
                      const subInstruction = generateInstructionBanner(
                        paperDetail.subject_name,
                        b.questions,
                        b.data.type,
                      );
                      return (
                        <div
                          key={`prev-sub-${b.data.subsection_id}`}
                          className="my-5 bg-indigo-50/20 p-5 rounded-xl border border-indigo-100 shadow-sm space-y-4"
                        >
                          {subInstruction && (
                            <p className="text-xs font-bold text-indigo-950 bg-white p-3 rounded-lg border border-indigo-200 shadow-sm">
                              {subInstruction}
                            </p>
                          )}
                          {b.data.content && (
                            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
                              <MarkdownContent content={b.data.content} />
                            </div>
                          )}
                          <div className="space-y-4 pl-3 border-l-4 border-indigo-300">
                            {b.questions.map((q: any) =>
                              renderQuestionBlock(q, false),
                            )}
                          </div>
                        </div>
                      );
                    }
                    return (
                      <div key={`prev-q-${b.data.question_id}`}>
                        {renderQuestionBlock(b.data, false)}
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>
      );
    }

    const isEnglishSubject =
      paperSubject?.subject_code === "NGA_AN" ||
      paperDetail.subject_name.toLowerCase().includes("tiếng anh");

    return (
      <div className="space-y-8 text-left max-w-7xl mx-auto pb-32">
        <div className="content-box flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <button
              className="text-blue-600 hover:underline flex items-center gap-2 mb-3 font-bold text-sm"
              onClick={() => {
                setPaperDetail(null);
                setSelectedPaperId(null);
              }}
            >
              <FiArrowLeft /> Trở về Bảng danh mục Đề thi
            </button>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-3xl font-black text-slate-900 tracking-tight">
                {paperDetail.paper_code}
              </h1>
              <span className="bg-slate-100 text-slate-800 px-3 py-1 rounded-md text-sm font-bold border border-slate-200">
                {paperDetail.subject_name}
              </span>
              <span className="bg-blue-50 text-blue-700 px-3 py-1 rounded-md text-sm font-bold border border-blue-200">
                {paperDetail.total_questions} Câu hỏi
              </span>
              <span className="bg-green-50 text-green-700 px-3 py-1 rounded-md text-sm font-bold border border-green-200">
                {paperDetail.versions_count} Đề hoán vị
              </span>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={() => setIsPreviewMode(true)}
              className="btn-secondary flex items-center gap-2 text-sm"
            >
              <FiEye /> Xem thử
            </button>
            <button
              onClick={() =>
                openAddSubsectionModal(paperStructure[0]?.key || "part1")
              }
              className="btn-secondary flex items-center gap-2 text-sm"
            >
              <FiPlus /> Lập vùng ngữ liệu
            </button>
            <button
              onClick={handleGenerateVersions}
              className="btn-secondary flex items-center gap-2 text-sm"
              disabled={paperDetail.is_finalized}
            >
              <FiShuffle /> Trộn đề
            </button>
            <button
              className="btn-primary flex items-center gap-2 text-sm font-bold tracking-wide uppercase"
              onClick={() =>
                examAPI
                  .finalizePaper(paperDetail.paper_id)
                  .then(() => loadPaperDetail(paperDetail.paper_id))
              }
              disabled={paperDetail.is_finalized}
            >
              <FiCheckCircle /> Phê duyệt
            </button>
          </div>
        </div>

        {(paperSubject?.subject_code === "NVVAN" ||
          paperDetail.subject_name === "Ngữ Văn") && (
          <div className="content-box border-amber-200 bg-amber-50/20">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-base text-amber-950 uppercase tracking-wide">
                Ngữ liệu dùng chung toàn bài:
              </h3>
              <button
                onClick={() => {
                  setEditingReadingMaterial(true);
                  setTempReadingMaterial(paperDetail.reading_material || "");
                }}
                className="text-sm font-bold text-amber-900 hover:underline bg-white px-3 py-1.5 rounded-lg border border-amber-300 shadow-sm"
              >
                Sửa nội dung
              </button>
            </div>
            {editingReadingMaterial ? (
              <div className="space-y-4 bg-white p-4 rounded-xl border border-amber-300">
                <MarkdownBox
                  label="Soạn thảo trích đoạn tác phẩm:"
                  value={tempReadingMaterial}
                  onChange={setTempReadingMaterial}
                  minHeight="min-h-[220px]"
                />
                <div className="flex justify-end gap-2.5 pt-2">
                  <button
                    onClick={() => setEditingReadingMaterial(false)}
                    className="btn-secondary py-2 text-sm"
                  >
                    Hủy
                  </button>
                  <button
                    onClick={() => {
                      examAPI
                        .updatePaperReadingMaterial(
                          paperDetail.paper_id,
                          tempReadingMaterial,
                        )
                        .then(() => {
                          toast.success("Đã lưu đoạn trích");
                          setEditingReadingMaterial(false);
                          loadPaperDetail(paperDetail.paper_id);
                        })
                        .catch(() => toast.error("Lỗi cập nhật"));
                    }}
                    className="btn-primary py-2 text-sm"
                  >
                    Lưu
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-white p-4 md:p-5 rounded-xl border border-amber-200 max-h-80 overflow-y-auto shadow-inner text-slate-900">
                {paperDetail.reading_material ? (
                  <MarkdownContent content={paperDetail.reading_material} />
                ) : (
                  <p className="text-slate-400 italic text-sm font-medium">
                    Chưa có trích đoạn tác phẩm nào được chèn.
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        <div className="space-y-8">
          {paperStructure.map((part) => {
            const blocks: any[] = [];
            subsectionsList
              .filter(
                (s) =>
                  (s.part === "reading"
                    ? "part1"
                    : s.part === "writing"
                      ? "part2"
                      : s.part) === part.key,
              )
              .forEach((sub) => {
                const subQs = mappedQuestions.filter(
                  (q) => String(q.subsection_id) === String(sub.subsection_id),
                );
                const minQ =
                  subQs.length > 0
                    ? Math.min(...subQs.map((q) => q.question_number))
                    : 9999;
                blocks.push({
                  type: "subsection",
                  data: sub,
                  questions: subQs,
                  order: minQ,
                });
              });

            const looseQs = mappedQuestions.filter(
              (q) => q.mappedPart === part.key && !q.subsection_id,
            );
            looseQs.forEach((q) => {
              blocks.push({
                type: "loose",
                data: q,
                questions: [q],
                order: q.question_number,
              });
            });
            blocks.sort((a, b) => a.order - b.order);

            const isReadingPart = isEnglishSubject && part.key.startsWith("r");
            const customTitlePreset = part.key.startsWith("rc")
              ? "Reading Passage"
              : part.key.startsWith("rf")
                ? "Guided Cloze Passage"
                : "Context Setup";

            const partInstructionBanner = generateInstructionBanner(
              paperDetail.subject_name,
              looseQs,
              undefined,
            );

            return (
              <div key={part.key} className="content-box p-0 overflow-hidden">
                <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-200 bg-slate-50 p-5 gap-4">
                  <div>
                    <h2 className="text-lg font-black text-blue-950 uppercase tracking-wide">
                      {part.label}
                    </h2>
                    <p className="text-xs text-slate-500 font-bold mt-1">
                      {part.points} •{" "}
                      {part.shuffle ? "Hệ thống tự động đảo" : "Cố định"}
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    {isReadingPart && (
                      <button
                        onClick={() =>
                          openAddSubsectionModal(
                            part.key,
                            customTitlePreset,
                            part.defaultSubType || "reading_comprehension",
                          )
                        }
                        className="bg-amber-100 hover:bg-amber-200 text-amber-950 font-bold px-3 py-2 rounded-lg text-xs transition-colors border border-amber-300 shadow-sm flex items-center gap-1.5"
                        title="Thêm đoạn văn chung cho nhóm câu hỏi"
                      >
                        <FiPlus size={16} /> Thêm Đoạn Ngữ Liệu
                      </button>
                    )}
                    <button
                      type='button'
                      onClick={() => openImportModal(part.key)}
                      className="btn-secondary px-3 py-2 text-xs flex items-center gap-1.5"
                    >
                      <FiUpload size={16} /> Nhập CSV
                    </button>
                    <button
                      type='button'
                      onClick={() => openAddQuestionModal(part.key)}
                      className="btn-primary px-3 py-2 text-xs flex items-center gap-1.5"
                    >
                      <FiPlus size={16} /> Thêm câu lẻ
                    </button>
                  </div>
                </div>

                {partInstructionBanner && (
                  <div className="bg-blue-50/60 px-5 py-3 border-b border-slate-200 text-xs text-blue-950 font-bold italic shadow-sm">
                    <span className="underline">Chỉ dẫn hệ thống:</span> "
                    {partInstructionBanner}"
                  </div>
                )}

                <div className="p-5 bg-white space-y-5">
                  {blocks.map((block, index) => {
                    return (
                      <div
                        key={
                          block.type === "subsection"
                            ? `sub-${block.data.subsection_id}`
                            : `q-${block.data.question_id}`
                        }
                        draggable={block.type !== "subsection"}
                        onDragStart={(e) => {
                          if (block.type !== "subsection") {
                            dragItem.current = index;
                            e.dataTransfer.effectAllowed = "move";
                          }
                        }}
                        onDragEnter={(e) => {
                          if (block.type !== "subsection") {
                            dragOverItem.current = index;
                            e.preventDefault();
                          }
                        }}
                        onDragOver={(e) => {
                          e.preventDefault();
                        }}
                        onDragEnd={() =>
                          block.type !== "subsection"
                            ? handleSort(part.key)
                            : null
                        }
                        className="content-box hover:border-blue-200 flex items-stretch gap-3 group p-4 shadow-sm"
                      >
                        {block.type !== "subsection" && (
                          <div
                            className="flex items-center justify-center cursor-move text-slate-300 group-hover:text-blue-600 px-1 transition-colors"
                            title="Kéo thả hoán vị"
                          >
                            <FiMenu size={20} />
                          </div>
                        )}

                        <div className="flex-1 overflow-hidden pointer-events-auto">
                          {block.type === "subsection" ? (
                            <div className="content-box bg-indigo-50/20 border-indigo-200 shadow-sm p-5 space-y-4">
                              <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-indigo-200 pb-3 gap-3">
                                <div className="flex items-center gap-2.5">
                                  <div
                                    draggable
                                    onDragStart={(e) => {
                                      dragItem.current = index;
                                      e.dataTransfer.effectAllowed = "move";
                                    }}
                                    onDragEnter={(e) => {
                                      dragOverItem.current = index;
                                      e.preventDefault();
                                    }}
                                    onDragEnd={() => handleSort(part.key)}
                                    className="cursor-move text-indigo-400 hover:text-indigo-900 p-1"
                                    title="Kéo thả nguyên cụm đoạn trích"
                                  >
                                    <FiMenu size={20} />
                                  </div>
                                  <span className="bg-indigo-100 text-indigo-900 text-xs font-black px-2 py-0.5 rounded uppercase tracking-wider">
                                    Passage Box
                                  </span>
                                  <h3 className="text-base font-bold text-indigo-950">
                                    {block.data.title ||
                                      "Đoạn văn đọc hiểu chung"}
                                  </h3>
                                </div>
                                <div className="flex items-center gap-2">
                                  <button
                                    onClick={() =>
                                      openAddQuestionModal(
                                        part.key,
                                        String(block.data.subsection_id),
                                      )
                                    }
                                    className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs py-1.5 px-3 rounded-lg flex items-center gap-1.5 shadow-sm transition-all"
                                  >
                                    <FiPlus size={14} /> Thêm câu con
                                  </button>
                                  <button
                                    onClick={() => {
                                      setSubsectionForm({
                                        title: block.data.title || "",
                                        content: block.data.content || "",
                                        type: block.data.type,
                                        shuffle_questions:
                                          block.data.shuffle_questions,
                                        shuffle_choices:
                                          block.data.shuffle_choices,
                                        shuffle_items: block.data.shuffle_items,
                                        part: block.data.part,
                                      });
                                      setIsEditingSubsection(true);
                                      setEditingSubsectionId(
                                        block.data.subsection_id,
                                      );
                                      setShowSubsectionModal(true);
                                    }}
                                    className="bg-white text-indigo-800 hover:bg-indigo-100 p-2 rounded-lg border border-indigo-200 transition-colors shadow-sm"
                                    title="Sửa nội dung"
                                  >
                                    <FiEdit size={15} />
                                  </button>
                                  <button
                                    onClick={() =>
                                      deleteSubsection(block.data.subsection_id)
                                    }
                                    className="bg-white text-red-600 hover:bg-red-50 p-2 rounded-lg border border-indigo-200 transition-colors shadow-sm"
                                    title="Xóa cụm"
                                  >
                                    <FiTrash2 size={15} />
                                  </button>
                                </div>
                              </div>

                              {generateInstructionBanner(
                                paperDetail.subject_name,
                                block.questions,
                                block.data.type,
                              ) && (
                                <p className="text-xs text-indigo-950 font-bold italic bg-white p-3 rounded-lg border border-indigo-200 shadow-sm">
                                  <span className="underline">
                                    Chỉ dẫn hệ thống:
                                  </span>{" "}
                                  "
                                  {generateInstructionBanner(
                                    paperDetail.subject_name,
                                    block.questions,
                                    block.data.type,
                                  )}
                                  "
                                </p>
                              )}

                              {block.data.content && (
                                <div className="content-box p-4 max-h-72 overflow-y-auto shadow-sm border-slate-200">
                                  <MarkdownContent
                                    content={block.data.content}
                                  />
                                </div>
                              )}

                              <div className="space-y-4 pl-3 md:pl-5 border-l-4 border-indigo-300 pt-2">
                                {block.questions
                                  .sort(
                                    (a: any, b: any) =>
                                      a.question_number - b.question_number,
                                  )
                                  .map((q: any, cIdx: number) => (
                                    <div
                                      key={`sub-q-${q.question_id}`}
                                      draggable
                                      onDragStart={(e) => {
                                        dragChildItem.current = cIdx;
                                        e.dataTransfer.effectAllowed = "move";
                                        e.stopPropagation();
                                      }}
                                      onDragEnter={(e) => {
                                        dragOverChildItem.current = cIdx;
                                        e.preventDefault();
                                        e.stopPropagation();
                                      }}
                                      onDragOver={(e) => {
                                        e.preventDefault();
                                        e.stopPropagation();
                                      }}
                                      onDragEnd={(e) => {
                                        e.stopPropagation();
                                        handleSortChild(
                                          block.data.subsection_id,
                                        );
                                      }}
                                      className="flex items-stretch gap-2.5 group/child"
                                    >
                                      <div
                                        className="flex items-center justify-center cursor-move text-indigo-300 hover:text-indigo-700 px-1 transition-colors"
                                        title="Kéo thả sắp xếp câu con"
                                      >
                                        <FiMenu size={18} />
                                      </div>
                                      <div className="flex-1">
                                        {renderQuestionBlock(q, true)}
                                      </div>
                                    </div>
                                  ))}
                                {block.questions.length === 0 && (
                                  <p className="text-xs text-indigo-500 font-bold italic">
                                    Vùng ngữ liệu rỗng. Bấm "Thêm câu con" ở
                                    trên.
                                  </p>
                                )}
                              </div>
                            </div>
                          ) : (
                            renderQuestionBlock(block.data, true)
                          )}
                        </div>
                      </div>
                    );
                  })}
                  {blocks.length === 0 && (
                    <p className="py-12 text-center text-slate-400 font-bold text-sm">
                      Chưa có câu hỏi trực thuộc vùng thi này.
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {showImportModal && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-2xs">
            <div className="content-box max-w-xl w-full p-0 overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <FiUpload className="text-blue-600" /> Import CSV
                </h3>
                <button
                  onClick={() => setShowImportModal(false)}
                  className="text-slate-400 hover:text-red-600 transition-colors"
                >
                  <FiXCircle size={24} />
                </button>
              </div>
              <form onSubmit={handleImportSubmit} className="p-6 space-y-5">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">
                    Định dạng nạp vào{" "}
                    <span className="text-blue-600 uppercase">
                      {importForm.part}
                    </span>
                    :
                  </label>
                  <select
                    className="input-field"
                    value={importForm.questionType}
                    onChange={(e) =>
                      setImportForm({
                        ...importForm,
                        questionType: e.target.value,
                      })
                    }
                  >
                    <option value="multiple_choice">
                      Trắc nghiệm 4 phương án (A, B, C, D)
                    </option>
                    <option value="true_false">
                      Trắc nghiệm Đúng/Sai (a, b, c, d)
                    </option>
                    <option value="short_answer">
                      Trả lời ngắn (Điền ký tự)
                    </option>
                  </select>
                </div>
                <div className="content-box bg-blue-50/80 border-blue-200 p-4 text-xs text-blue-950 shadow-sm">
                  <p className="font-bold mb-1.5 flex items-center gap-1.5 text-blue-900">
                    <FiFileText /> Chuẩn Header dòng đầu: <button
                    type='button'
                    onClick={() =>
                      exportAPI.downloadTemplate(
                        importForm.questionType === 'multiple_choice'
                          ? 'question_mc'
                          : importForm.questionType === 'true_false'
                          ? 'question_tf'
                          : 'question_sa'
                      )
                    }
                    className="btn-secondary px-3 py-2 text-xs flex items-center gap-1.5"
                  >
                    <FiDownload size={16} /> Tải mẫu CSV
                  </button>
                  </p>
                  <p className="font-mono bg-white p-2.5 border border-blue-300 rounded-lg overflow-x-auto text-xs font-bold shadow-inner">
                    {getCsvFormatGuide()}
                  </p>
                  <p>Có thể để cột <strong>DinhHuong</strong> trống. Các giá trị chấp nhận trong cột <strong>DinhHuong</strong>: <code>Chung</code>, <code>ICT</code>, <code>CS</code>.</p>
                </div>
                <div className="content-box border-2 border-dashed border-slate-300 p-8 text-center hover:border-blue-500 hover:bg-blue-50/20 cursor-pointer relative transition-all shadow-none">
                  <input
                    type="file"
                    accept=".csv"
                    onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    required
                  />
                  <div className="space-y-2">
                    <p className="font-bold text-sm text-blue-600">
                      {importFile
                        ? importFile.name
                        : "Bấm chọn hoặc kéo thả file CSV"}
                    </p>
                    <p className="text-xs text-slate-400 font-medium">
                      {importFile
                        ? `${(importFile.size / 1024).toFixed(1)} KB`
                        : "Hỗ trợ .csv định dạng UTF-8"}
                    </p>
                  </div>
                </div>
                <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
                  <button
                    type="button"
                    className="btn-secondary py-2 text-sm"
                    onClick={() => setShowImportModal(false)}
                  >
                    Hủy
                  </button>
                  <button
                    type="submit"
                    className="btn-primary py-2 text-sm"
                    disabled={isImporting || !importFile}
                  >
                    {isImporting ? "Đang nạp..." : "Xác nhận nạp"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {showSubsectionModal && (
          <div className="fixed inset-0 z-[90] flex items-center justify-center p-4 bg-black/60 backdrop-blur-2xs">
            <div className="content-box max-w-4xl w-full p-0 overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
                <h3 className="text-lg font-bold text-slate-900">
                  {isEditingSubsection
                    ? "Sửa Vùng Ngữ liệu"
                    : "Tạo Vùng Ngữ liệu chung"}
                </h3>
                <button
                  onClick={() => setShowSubsectionModal(false)}
                  className="text-slate-400 hover:text-red-600 transition-colors"
                >
                  <FiXCircle size={24} />
                </button>
              </div>
              <form
                onSubmit={handleSaveSubsection}
                className="p-6 space-y-5 max-h-[80vh] overflow-y-auto"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">
                      Tiêu đề vùng (KHÔNG gõ đề vào đây):
                    </label>
                    <input
                      type="text"
                      className="input-field font-bold"
                      placeholder="VD: Reading Passage 1..."
                      value={subsectionForm.title}
                      onChange={(e) =>
                        setSubsectionForm({
                          ...subsectionForm,
                          title: e.target.value,
                        })
                      }
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">
                      Thuộc phần:
                    </label>
                    <select
                      className="input-field bg-slate-50 font-bold"
                      value={subsectionForm.part}
                      onChange={(e) =>
                        setSubsectionForm({
                          ...subsectionForm,
                          part: e.target.value,
                        })
                      }
                    >
                      {paperStructure.map((p) => (
                        <option key={p.key} value={p.key}>
                          {p.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-1">
                    Cơ chế hiển thị bài đọc:
                  </label>
                  <select
                    className="input-field text-blue-900 font-bold"
                    value={subsectionForm.type}
                    onChange={(e) =>
                      setSubsectionForm({
                        ...subsectionForm,
                        type: e.target.value as any,
                      })
                    }
                  >
                    <option value="normal">Tiêu chuẩn (Văn bản độc lập)</option>
                    <option value="reading_comprehension">
                      Đoạn văn Đọc hiểu (Reading Comprehension Passage)
                    </option>
                    <option value="reading_fill_in">
                      Đoạn văn Điền khuyết (Tự thay thế ___ thành số câu)
                    </option>
                    <option value="arrangement_correction">
                      Đoạn văn Sắp xếp câu / Sửa lỗi sai
                    </option>
                  </select>
                </div>
                <MarkdownBox
                  label="Nội dung văn bản (Passage Text):"
                  value={subsectionForm.content}
                  onChange={(v) =>
                    setSubsectionForm({ ...subsectionForm, content: v })
                  }
                  minHeight="min-h-[360px]"
                />
                <div className="content-box bg-slate-50 border-slate-200 p-4 flex flex-wrap gap-6 text-sm font-bold shadow-sm">
                  <label className="flex items-center gap-2 cursor-pointer text-slate-800">
                    <input
                      type="checkbox"
                      checked={subsectionForm.shuffle_questions}
                      onChange={(e) =>
                        setSubsectionForm({
                          ...subsectionForm,
                          shuffle_questions: e.target.checked,
                        })
                      }
                      className="rounded text-blue-600 w-4 h-4 focus:ring-0"
                    />{" "}
                    Đảo câu hỏi con
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer text-slate-800">
                    <input
                      type="checkbox"
                      checked={subsectionForm.shuffle_choices}
                      onChange={(e) =>
                        setSubsectionForm({
                          ...subsectionForm,
                          shuffle_choices: e.target.checked,
                        })
                      }
                      className="rounded text-blue-600 w-4 h-4 focus:ring-0"
                    />{" "}
                    Đảo phương án A,B,C,D
                  </label>
                </div>
                <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
                  <button
                    type="button"
                    className="btn-secondary py-2 text-sm"
                    onClick={() => setShowSubsectionModal(false)}
                  >
                    Hủy
                  </button>
                  <button type="submit" className="btn-primary py-2 text-sm">
                    Lưu
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {showQuestionModal && (
          <div className="fixed inset-0 z-[80] flex items-center justify-center p-4 bg-black/60 backdrop-blur-2xs">
            <div className="content-box max-w-4xl w-full p-0 overflow-hidden flex flex-col h-[85vh]">
              <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center bg-slate-50 shrink-0">
                <h3 className="text-lg font-bold text-slate-900">
                  {isEditingQuestion ? "Sửa Câu hỏi thi" : "Tạo Câu hỏi mới"}
                </h3>
                <button
                  onClick={() => setShowQuestionModal(false)}
                  className="text-slate-400 hover:text-red-600 transition-colors"
                >
                  <FiXCircle size={24} />
                </button>
              </div>
              <form
                onSubmit={handleSaveQuestion}
                className="p-6 flex-1 overflow-y-auto space-y-5"
              >
                <div className="content-box grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-50 border-slate-200 p-4 shadow-sm">
                  <div>
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                      Gán vào mục:
                    </label>
                    <select
                      className="input-field font-bold py-2"
                      value={questionForm.part}
                      onChange={(e) => {
                        const p = e.target.value;
                        const targetPartObj = paperStructure.find(
                          (x) => x.key === p,
                        );
                        setQuestionForm({
                          ...questionForm,
                          part: p,
                          question_type:
                            targetPartObj?.type || "multiple_choice",
                        });
                      }}
                    >
                      {paperStructure.map((p) => (
                        <option key={p.key} value={p.key}>
                          {p.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                      Định dạng:
                    </label>
                    <select
                      className="input-field font-bold py-2 text-blue-900"
                      value={questionForm.question_type}
                      onChange={(e) =>
                        setQuestionForm({
                          ...questionForm,
                          question_type: e.target.value,
                        })
                      }
                    >
                      <option value="multiple_choice">
                        Trắc nghiệm 4 lựa chọn
                      </option>
                      <option value="true_false">Trắc nghiệm Đúng/Sai</option>
                      <option value="short_answer">Trả lời ngắn</option>
                      <option value="essay">Tự luận viết tay</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                      Điểm số:
                    </label>
                    <input
                      type="number"
                      step="0.05"
                      min="0"
                      max="10"
                      className="input-field font-black text-blue-600 py-2"
                      value={questionForm.points}
                      onChange={(e) =>
                        setQuestionForm({
                          ...questionForm,
                          points: e.target.value,
                        })
                      }
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">
                      Thuộc vùng ngữ liệu (Cho phép chuyển đổi linh hoạt):
                    </label>
                    <select
                      className="input-field font-medium"
                      value={questionForm.subsection_id || ""}
                      onChange={(e) =>
                        setQuestionForm({
                          ...questionForm,
                          subsection_id: e.target.value,
                        })
                      }
                    >
                      <option value="">
                        -- Độc lập (Đưa ra khỏi Passage về luồng tự do) --
                      </option>
                      {subsectionsList
                        .filter(
                          (s) =>
                            (s.part === "reading"
                              ? "part1"
                              : s.part === "writing"
                                ? "part2"
                                : s.part) === questionForm.part,
                        )
                        .map((sub) => (
                          <option
                            key={sub.subsection_id}
                            value={sub.subsection_id}
                          >
                            [Passage] {sub.title || `ID: ${sub.subsection_id}`}
                          </option>
                        ))}
                    </select>
                  </div>
                  {paperSubject?.subject_code === "TIN_HO" &&
                    questionForm.part === "part2" && (
                      <div>
                        <label className="block text-sm font-bold text-blue-800 mb-1">
                          Định hướng chuyên sâu (Tin học):
                        </label>
                        <select
                          className="input-field font-bold bg-blue-50/30"
                          value={questionForm.informatics_track}
                          onChange={(e) =>
                            setQuestionForm({
                              ...questionForm,
                              informatics_track: e.target.value,
                            })
                          }
                        >
                          <option value="">-- Dành chung --</option>
                          <option value="computer_science">
                            Khoa học Máy tính (CS)
                          </option>
                          <option value="applied_informatics">
                            Tin học Ứng dụng (ICT)
                          </option>
                        </select>
                      </div>
                    )}
                </div>
                <MarkdownBox
                  label="Nội dung đề bài:"
                  value={questionForm.question_text}
                  onChange={(v) =>
                    setQuestionForm({ ...questionForm, question_text: v })
                  }
                  minHeight="min-h-[120px]"
                />
                <div className="border-t border-slate-200 pt-5">
                  {questionForm.question_type === "multiple_choice" && (
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <label className="text-sm font-bold text-slate-900 uppercase block">
                          4 phương án & Chọn đáp án chuẩn:
                        </label>
                        <div className="flex items-center gap-2 bg-blue-50 px-3 py-1 rounded-lg border border-blue-200 text-xs text-blue-950 font-bold">
                          <span>ĐÁP ÁN:</span>
                          <select
                            className="bg-white border border-blue-300 rounded font-black px-2 py-0.5 text-blue-700"
                            value={questionForm.correct_answer}
                            onChange={(e) =>
                              setQuestionForm({
                                ...questionForm,
                                correct_answer: e.target.value,
                              })
                            }
                            required
                          >
                            <option value="">- Chọn -</option>
                            <option value="A">A</option>
                            <option value="B">B</option>
                            <option value="C">C</option>
                            <option value="D">D</option>
                          </select>
                        </div>
                      </div>
                      <div className="grid grid-cols-1 gap-3">
                        {["A", "B", "C", "D"].map((char, index) => (
                          <div
                            key={char}
                            className={`content-box p-4 border-2 transition-all shadow-sm ${questionForm.correct_answer === char ? "bg-green-50/60 border-green-400" : "bg-slate-50 border-slate-200"}`}
                          >
                            <div className="flex items-center gap-2 mb-2">
                              <span
                                className={`w-5 h-5 rounded-full flex items-center justify-center font-black text-xs ${questionForm.correct_answer === char ? "bg-green-600 text-white" : "bg-slate-300 text-slate-700"}`}
                              >
                                {char}
                              </span>
                              <span className="text-xs font-bold text-slate-500 uppercase">
                                Nội dung phương án:
                              </span>
                            </div>
                            <textarea
                              className="input-field font-mono text-sm min-h-[60px] bg-white"
                              placeholder={`Nhập phương án ${char}...`}
                              value={choiceDrafts[index]}
                              onChange={(e) => {
                                const arr = [...choiceDrafts];
                                arr[index] = e.target.value;
                                setChoiceDrafts(arr);
                              }}
                              required
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {questionForm.question_type === "true_false" && (
                    <div className="space-y-4">
                      <label className="text-sm font-bold text-slate-900 uppercase block">
                        Cấu hình 4 ý hỏi Đúng/Sai:
                      </label>
                      <div className="space-y-3">
                        {["a", "b", "c", "d"].map((char, idx) => (
                          <div
                            key={char}
                            className="content-box bg-slate-50 p-3.5 border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center gap-3"
                          >
                            <span className="w-6 h-6 bg-slate-900 text-white rounded-full flex items-center justify-center font-bold text-xs shrink-0">
                              {char}
                            </span>
                            <div className="flex-1 w-full">
                              <input
                                type="text"
                                className="input-field font-mono text-sm bg-white"
                                placeholder={`Nhập ý hỏi ${char}...`}
                                value={trueFalseDrafts[idx].text}
                                onChange={(e) => {
                                  const arr = [...trueFalseDrafts];
                                  arr[idx].text = e.target.value;
                                  setTrueFalseDrafts(arr);
                                }}
                                required
                              />
                            </div>
                            <div className="flex gap-2 shrink-0 w-full md:w-auto justify-end">
                              <button
                                type="button"
                                onClick={() => {
                                  const arr = [...trueFalseDrafts];
                                  arr[idx].correct_value = "true";
                                  setTrueFalseDrafts(arr);
                                }}
                                className={`px-3 py-1.5 rounded-md font-bold text-xs transition-colors ${trueFalseDrafts[idx].correct_value === "true" ? "bg-green-600 text-white shadow-sm" : "bg-slate-200 text-slate-600 hover:bg-slate-300"}`}
                              >
                                Đúng
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  const arr = [...trueFalseDrafts];
                                  arr[idx].correct_value = "false";
                                  setTrueFalseDrafts(arr);
                                }}
                                className={`px-3 py-1.5 rounded-md font-bold text-xs transition-colors ${trueFalseDrafts[idx].correct_value === "false" ? "bg-red-600 text-white shadow-sm" : "bg-slate-200 text-slate-600 hover:bg-slate-300"}`}
                              >
                                Sai
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {questionForm.question_type === "short_answer" && (
                    <div className="space-y-3">
                      <label className="text-sm font-bold text-slate-900 uppercase block">
                        Chuỗi chốt đáp án (Tối đa 4 ô):
                      </label>
                      <div className="flex gap-3 justify-start py-1">
                        {[0, 1, 2, 3].map((i) => (
                          <input
                            key={i}
                            id={`short_ans_setup_${i}`}
                            type="text"
                            maxLength={1}
                            className="w-14 h-14 text-2xl font-black text-center border-2 border-blue-400 rounded-xl focus:border-blue-600 focus:outline-none uppercase bg-blue-50/20 text-blue-950 shadow-inner"
                            value={shortAnswerCells[i]}
                            onChange={(e) => {
                              const val = e.target.value;
                              if (val && !/^[0-9\-,A-Za-z]$/.test(val)) return;
                              const arr = [...shortAnswerCells];
                              arr[i] = val.toUpperCase();
                              setShortAnswerCells(arr);
                              if (val && i < 3)
                                document
                                  .getElementById(`short_ans_setup_${i + 1}`)
                                  ?.focus();
                            }}
                            onKeyDown={(e) => {
                              if (
                                e.key === "Backspace" &&
                                !shortAnswerCells[i] &&
                                i > 0
                              ) {
                                document
                                  .getElementById(`short_ans_setup_${i - 1}`)
                                  ?.focus();
                              }
                            }}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                  {questionForm.question_type === "essay" && (
                    <div className="space-y-4">
                      <MarkdownBox
                        label="Gợi ý đáp án / Thang chấm:"
                        value={questionForm.correct_answer || ""}
                        onChange={(v) =>
                          setQuestionForm({
                            ...questionForm,
                            correct_answer: v,
                          })
                        }
                        minHeight="min-h-[140px]"
                      />
                      <div className="content-box bg-amber-50/50 border-amber-200 p-4 grid grid-cols-1 md:grid-cols-2 gap-4 shadow-sm">
                        <div>
                          <label className="block text-xs font-bold text-amber-950 uppercase tracking-wider mb-1">
                            Tối đa số chữ (Words):
                          </label>
                          <input
                            type="number"
                            min="1"
                            className="input-field bg-white font-bold"
                            placeholder="VD: 650"
                            value={questionForm.max_words}
                            onChange={(e) =>
                              setQuestionForm({
                                ...questionForm,
                                max_words: e.target.value,
                              })
                            }
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-bold text-amber-950 uppercase tracking-wider mb-1">
                            Tối đa ký tự (Chars):
                          </label>
                          <input
                            type="number"
                            min="1"
                            className="input-field bg-white font-bold"
                            placeholder="VD: 1200"
                            value={questionForm.max_chars}
                            onChange={(e) =>
                              setQuestionForm({
                                ...questionForm,
                                max_chars: e.target.value,
                              })
                            }
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                <div className="content-box bg-slate-50 border-slate-200 p-4 flex items-center justify-between shadow-sm">
                  <span className="text-sm font-bold text-slate-700">
                    Cơ chế hoán vị:
                  </span>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={questionForm.shuffle_enabled ?? true}
                      onChange={(e) =>
                        setQuestionForm({
                          ...questionForm,
                          shuffle_enabled: e.target.checked,
                        })
                      }
                      className="rounded text-blue-600 w-5 h-5 focus:ring-0"
                    />
                    <span className="text-sm font-bold text-blue-950">
                      Cho phép hệ thống tự động hoán vị câu này
                    </span>
                  </label>
                </div>
                <div className="content-box flex justify-end gap-3 p-3 sticky bottom-0 bg-white shadow-md border-t border-slate-200">
                  <button
                    type="button"
                    className="btn-secondary py-2 text-sm"
                    onClick={() => setShowQuestionModal(false)}
                  >
                    Hủy
                  </button>
                  <button
                    type="submit"
                    className="btn-primary py-2 px-8 text-sm font-bold tracking-wide uppercase"
                  >
                    Lưu câu hỏi
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-8 text-left max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-200 pb-4 gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-black text-slate-900">
            Quản Trị Kỳ Thi & Đề Thi
          </h1>
          <p className="text-sm text-slate-500 font-medium mt-1">
            Cấu hình ngân hàng đề gốc, phân bổ mã đề và khung giờ thi.
          </p>
        </div>
        <div className="content-box p-1 bg-slate-100 border-slate-200 flex w-fit shadow-none">
          <button
            className={`px-5 py-2 rounded-lg font-bold text-sm transition-all ${activeTab === "sessions" ? "bg-white text-blue-900 shadow-sm" : "text-slate-600 hover:text-slate-900"}`}
            onClick={() => setActiveTab("sessions")}
          >
            Kỳ Thi / Lịch
          </button>
          <button
            className={`px-5 py-2 rounded-lg font-bold text-sm transition-all ${activeTab === "papers" ? "bg-white text-blue-900 shadow-sm" : "text-slate-600 hover:text-slate-900"}`}
            onClick={() => setActiveTab("papers")}
          >
            Ngân Hàng Đề
          </button>
        </div>
      </div>
      {activeTab === "sessions" ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="space-y-6">
            <div className="content-box space-y-4">
              <h3 className="font-black text-base text-slate-900 border-b border-slate-100 pb-3">
                Tạo Kỳ Thi
              </h3>
              <form onSubmit={createSession} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                    Tên kỳ thi:
                  </label>
                  <input
                    type="text"
                    className="input-field font-bold"
                    placeholder="VD: Khảo sát Lần 1..."
                    value={sessionForm.session_name}
                    onChange={(e) =>
                      setSessionForm({
                        ...sessionForm,
                        session_name: e.target.value,
                      })
                    }
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                      Bắt đầu:
                    </label>
                    <input
                      type="date"
                      className="input-field"
                      value={sessionForm.start_date}
                      onChange={(e) =>
                        setSessionForm({
                          ...sessionForm,
                          start_date: e.target.value,
                        })
                      }
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                      Kết thúc:
                    </label>
                    <input
                      type="date"
                      className="input-field"
                      value={sessionForm.end_date}
                      onChange={(e) =>
                        setSessionForm({
                          ...sessionForm,
                          end_date: e.target.value,
                        })
                      }
                      required
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  className="btn-primary w-full py-2.5 text-sm"
                >
                  Khởi tạo
                </button>
              </form>
            </div>
            <div className="content-box space-y-4">
              <h3 className="font-black text-base text-slate-900 border-b border-slate-100 pb-3">
                Phân Bổ Lịch Thi
              </h3>
              <form onSubmit={createSchedule} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                    Kỳ thi:
                  </label>
                  <select
                    className="input-field font-bold"
                    value={scheduleForm.exam_session_id}
                    onChange={(e) =>
                      setScheduleForm({
                        ...scheduleForm,
                        exam_session_id: e.target.value,
                      })
                    }
                    required
                  >
                    <option value="">- Chọn -</option>
                    {sessions.map((s) => (
                      <option key={s.exam_session_id} value={s.exam_session_id}>
                        {s.session_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                    Môn thi:
                  </label>
                  <select
                    className="input-field font-bold"
                    value={scheduleForm.subject_id}
                    onChange={(e) =>
                      setScheduleForm({
                        ...scheduleForm,
                        subject_id: e.target.value,
                      })
                    }
                    required
                  >
                    <option value="">- Chọn -</option>
                    {subjects.map((sub) => (
                      <option key={sub.subject_id} value={sub.subject_id}>
                        {sub.subject_name} ({sub.duration_minutes}p)
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                    Ngày thi:
                  </label>
                  <input
                    type="date"
                    className="input-field"
                    value={scheduleForm.exam_date}
                    onChange={(e) =>
                      setScheduleForm({
                        ...scheduleForm,
                        exam_date: e.target.value,
                      })
                    }
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                      Giờ bắt đầu:
                    </label>
                    <input
                      type="time"
                      className="input-field font-mono font-bold"
                      value={scheduleForm.start_time}
                      onChange={(e) =>
                        setScheduleForm({
                          ...scheduleForm,
                          start_time: e.target.value,
                        })
                      }
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                      Giờ kết thúc:
                    </label>
                    <input
                      type="time"
                      className="input-field font-mono font-bold"
                      value={scheduleForm.end_time}
                      onChange={(e) =>
                        setScheduleForm({
                          ...scheduleForm,
                          end_time: e.target.value,
                        })
                      }
                      required
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  className="btn-primary w-full py-2.5 text-sm"
                >
                  Gán lịch
                </button>
              </form>
            </div>
          </div>
          <div className="lg:col-span-2 space-y-6">
            <div className="content-box">
              <h3 className="font-black text-base text-slate-900 border-b border-slate-100 pb-3 mb-4">
                Danh Sách Kỳ Thi
              </h3>
              <div className="space-y-4">
                {sessions.map((s) => {
                  const scheds = schedules.filter(
                    (sc) => sc.session_name === s.session_name,
                  );
                  return (
                    <div
                      key={s.exam_session_id}
                      className="content-box p-5 bg-white shadow-sm"
                    >
                      <div className="flex justify-between items-start gap-3 mb-3">
                        <div>
                          <h4 className="font-black text-base text-blue-950">
                            {s.session_name}
                          </h4>
                          <p className="text-xs text-slate-500 font-medium mt-0.5">
                            Thời gian: {s.start_date} tới {s.end_date}
                          </p>
                        </div>
                        <span
                          className={`px-2.5 py-1 rounded-md text-xs font-bold uppercase ${s.is_published ? "bg-green-50 text-green-700" : "bg-amber-50 text-amber-700"}`}
                        >
                          {s.is_published ? "Đã công bố" : "Bản nháp"}
                        </span>
                      </div>
                      <div className="space-y-2 mt-3 pt-3 border-t border-slate-100">
                        <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                          Lịch các môn:
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {scheds.map((sc) => (
                            <div
                              key={sc.schedule_id}
                              className="content-box bg-slate-50 p-3 border-slate-200 text-sm shadow-sm"
                            >
                              <p className="font-bold text-slate-800">
                                {sc.subject_name}
                              </p>
                              <p className="text-slate-500 text-xs mt-0.5">
                                Ngày: {sc.exam_date} ({sc.start_time} -{" "}
                                {sc.end_time})
                              </p>
                            </div>
                          ))}{" "}
                          {scheds.length === 0 && (
                            <p className="text-xs text-slate-400 italic font-medium">
                              Chưa phân bổ lịch.
                            </p>
                          )}
                        </div>
                      </div>
                      {!s.is_published && (
                        <div className="flex justify-end mt-4 pt-3 border-t border-slate-100">
                          <button
                            onClick={() => publishSession(s.exam_session_id)}
                            className="btn-secondary py-1.5 px-4 text-xs font-bold text-blue-700"
                          >
                            Công bố
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}{" "}
                {sessions.length === 0 && (
                  <p className="py-8 text-center text-slate-400 font-bold text-sm">
                    Chưa có dữ liệu.
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="space-y-6">
            <div className="content-box space-y-4">
              <h3 className="font-black text-base text-slate-900 border-b border-slate-100 pb-3">
                Tạo Mã Đề Gốc
              </h3>
              <form onSubmit={createPaper} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                    Kỳ thi:
                  </label>
                  <select
                    className="input-field font-bold"
                    value={paperForm.exam_session_id}
                    onChange={(e) => {
                      setPaperForm({
                        ...paperForm,
                        exam_session_id: e.target.value,
                      });
                      setSelectedSessionId(e.target.value);
                    }}
                    required
                  >
                    <option value="">- Chọn -</option>
                    {sessions.map((s) => (
                      <option key={s.exam_session_id} value={s.exam_session_id}>
                        {s.session_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                    Môn thi:
                  </label>
                  <select
                    className="input-field font-bold"
                    value={paperForm.subject_id}
                    onChange={(e) =>
                      setPaperForm({ ...paperForm, subject_id: e.target.value })
                    }
                    required
                  >
                    <option value="">- Chọn -</option>
                    {subjects.map((sub) => (
                      <option key={sub.subject_id} value={sub.subject_id}>
                        {sub.subject_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                    Mã đề (Bản Master):
                  </label>
                  <input
                    type="text"
                    className="input-field font-black uppercase tracking-wide"
                    placeholder="VD: 101, GOC..."
                    value={paperForm.paper_code}
                    onChange={(e) =>
                      setPaperForm({ ...paperForm, paper_code: e.target.value })
                    }
                    required
                  />
                </div>
                <div className="content-box bg-slate-50 p-3 border-slate-200 shadow-sm">
                  <label className="flex items-center gap-2 cursor-pointer text-sm font-bold text-slate-800">
                    <input
                      type="checkbox"
                      checked={paperForm.randomization_enabled}
                      onChange={(e) =>
                        setPaperForm({
                          ...paperForm,
                          randomization_enabled: e.target.checked,
                        })
                      }
                      className="rounded text-blue-600 focus:ring-0 w-4 h-4"
                    />{" "}
                    Bật trộn tự động
                  </label>
                </div>
                <button
                  type="submit"
                  className="btn-primary w-full py-2.5 text-sm"
                >
                  Tạo đề gốc
                </button>
              </form>
            </div>
          </div>
          <div className="lg:col-span-2 space-y-4">
            <div className="content-box flex items-center justify-between p-4 shadow-sm">
              <span className="text-sm font-bold text-slate-700">
                Lọc theo Kỳ thi:
              </span>
              <select
                className="input-field w-72 bg-slate-50 py-1.5 text-sm font-bold"
                value={selectedSessionId}
                onChange={(e) => setSelectedSessionId(e.target.value)}
              >
                <option value="">- Toàn bộ -</option>
                {sessions.map((s) => (
                  <option key={s.exam_session_id} value={s.exam_session_id}>
                    {s.session_name}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {papers.map((p) => (
                <div
                  key={p.paper_id}
                  className="content-box hover:border-blue-400 transition-all flex flex-col justify-between h-44 p-5 shadow-sm"
                >
                  <div>
                    <div className="flex justify-between items-start">
                      <span className="bg-blue-600 text-white font-black text-xs px-2.5 py-1 rounded-md">
                        {p.paper_code}
                      </span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-md font-bold uppercase ${p.is_finalized ? "bg-slate-100 text-slate-500" : "bg-green-50 text-green-700"}`}
                      >
                        {p.is_finalized ? "Đã chốt" : "Đang soạn"}
                      </span>
                    </div>
                    <h4 className="font-black text-base text-slate-900 mt-3">
                      {p.subject_name}
                    </h4>
                    <p
                      className="text-xs text-slate-500 font-medium line-clamp-1 mt-0.5"
                      title={p.session_name}
                    >
                      {p.session_name}
                    </p>
                  </div>
                  <div className="border-t border-slate-100 pt-3 mt-3 flex justify-between items-center">
                    <div className="text-xs text-slate-600 font-medium">
                      <span className="font-black text-blue-900">
                        {p.total_questions}
                      </span>{" "}
                      câu •{" "}
                      <span className="font-black text-green-700">
                        {p.versions}
                      </span>{" "}
                      đề
                    </div>
                    <button
                      onClick={() => loadPaperDetail(p.paper_id)}
                      className="btn-primary py-1.5 px-4 text-xs font-bold"
                    >
                      Soạn
                    </button>
                  </div>
                </div>
              ))}
              {papers.length === 0 && (
                <div className="content-box col-span-2 py-12 text-center shadow-sm">
                  <p className="text-slate-400 font-bold text-sm">
                    Chưa có đề gốc.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
