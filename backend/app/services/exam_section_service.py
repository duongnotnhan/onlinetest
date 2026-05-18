"""Exam Section Service - Quản lý Section, Passage, và Question trong Section"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app import db
from app.models import (ExamPaper, Question, QuestionPassage, QuestionSection,
                        QuestionSectionType)
from app.services.rich_text_service import RichTextService


class ExamSectionService:
    """Service quản lý Question Sections"""

    @staticmethod
    def get_or_create_section_type(
        section_type_key: str,
    ) -> Optional[QuestionSectionType]:
        """
        Lấy hoặc tạo Section Type theo key

        Args:
            section_type_key: Mã key của section type (e.g., 'reading_comprehension')

        Returns:
            QuestionSectionType object hoặc None
        """
        section_type = QuestionSectionType.query.filter_by(
            section_type_key=section_type_key
        ).first()

        return section_type

    @staticmethod
    def create_section(
        paper_id: int,
        section_type_key: str = None,
        section_name: str = None,
        section_description: str = None,
        display_order: int = None,
        created_by: int = None,
    ) -> Tuple[bool, str, Optional[QuestionSection]]:
        """
        Tạo mới một Question Section

        Args:
            paper_id: ID của Exam Paper
            section_type_key: Mã key của section type
            section_name: Tên của section
            section_description: Mô tả của section
            display_order: Thứ tự hiển thị
            created_by: User ID tạo section

        Returns:
            Tuple (success: bool, message: str, section: QuestionSection or None)
        """
        try:
            # Kiểm tra paper tồn tại
            paper = ExamPaper.query.get(paper_id)
            if not paper:
                return False, "Exam Paper không tồn tại", None

            # Nếu chưa có display_order, lấy max + 1
            if display_order is None:
                last_section = (
                    QuestionSection.query.filter_by(paper_id=paper_id)
                    .order_by(QuestionSection.display_order.desc())
                    .first()
                )
                display_order = (
                    last_section.display_order +
                    1) if last_section else 1

            # Lấy section type nếu có
            section_type_id = None
            if section_type_key:
                section_type = ExamSectionService.get_or_create_section_type(
                    section_type_key
                )
                if section_type:
                    section_type_id = section_type.section_type_id

            # Tạo section
            section = QuestionSection(
                paper_id=paper_id,
                section_type_id=section_type_id,
                section_name=section_name,
                section_description=section_description,
                display_order=display_order,
                created_by=created_by,
                is_visible=True,
            )

            db.session.add(section)
            db.session.commit()

            return True, "Tạo Section thành công", section

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi tạo section: {str(e)}", None

    @staticmethod
    def get_section(section_id: int) -> Optional[QuestionSection]:
        """Lấy section theo ID"""
        return QuestionSection.query.get(section_id)

    @staticmethod
    def get_sections_by_paper(paper_id: int) -> List[QuestionSection]:
        """Lấy tất cả section của một paper"""
        return (
            QuestionSection.query.filter_by(paper_id=paper_id, is_visible=True)
            .order_by(QuestionSection.display_order)
            .all()
        )

    @staticmethod
    def update_section(
        section_id: int,
        section_name: str = None,
        section_description: str = None,
        updated_by: int = None,
    ) -> Tuple[bool, str]:
        """
        Cập nhật section

        Args:
            section_id: ID của section
            section_name: Tên mới
            section_description: Mô tả mới
            updated_by: User ID cập nhật

        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            section = QuestionSection.query.get(section_id)
            if not section:
                return False, "Section không tồn tại"

            if section_name:
                section.section_name = section_name

            if section_description:
                section.section_description = section_description

            if updated_by:
                section.updated_by = updated_by

            section.updated_at = datetime.utcnow()

            db.session.commit()

            return True, "Cập nhật section thành công"

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi cập nhật section: {str(e)}"

    @staticmethod
    def delete_section(section_id: int) -> Tuple[bool, str]:
        """
        Xóa section (soft delete)

        Args:
            section_id: ID của section

        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            section = QuestionSection.query.get(section_id)
            if not section:
                return False, "Section không tồn tại"

            # Soft delete
            section.is_visible = False
            db.session.commit()

            return True, "Xóa section thành công"

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi xóa section: {str(e)}"

    @staticmethod
    def add_passage(
        section_id: int,
        passage_text: str,
        passage_title: str = None,
        author_name: str = None,
        source_info: str = None,
        display_order: int = None,
        created_by: int = None,
        sanitize: bool = True,
    ) -> Tuple[bool, str, Optional[QuestionPassage]]:
        """
        Thêm passage cho section

        Args:
            section_id: ID của section
            passage_text: Nội dung passage
            passage_title: Tiêu đề passage
            author_name: Tên tác giả
            source_info: Thông tin nguồn
            display_order: Thứ tự hiển thị
            created_by: User ID tạo passage
            sanitize: Có sanitize HTML hay không

        Returns:
            Tuple (success: bool, message: str, passage: QuestionPassage or None)
        """
        try:
            # Kiểm tra section tồn tại
            section = QuestionSection.query.get(section_id)
            if not section:
                return False, "Section không tồn tại", None

            # Sanitize HTML nếu cần
            if sanitize:
                passage_text = RichTextService.sanitize_html(passage_text)

            # Lấy display_order nếu chưa có
            if display_order is None:
                last_passage = (
                    QuestionPassage.query.filter_by(section_id=section_id)
                    .order_by(QuestionPassage.display_order.desc())
                    .first()
                )
                display_order = (
                    last_passage.display_order +
                    1) if last_passage else 1

            # Tạo passage
            passage = QuestionPassage(
                section_id=section_id,
                passage_text=passage_text,
                passage_title=passage_title,
                author_name=author_name,
                source_info=source_info,
                display_order=display_order,
                created_by=created_by,
                is_visible=True,
            )

            db.session.add(passage)
            db.session.commit()

            return True, "Thêm passage thành công", passage

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi thêm passage: {str(e)}", None

    @staticmethod
    def get_passages_by_section(section_id: int) -> List[QuestionPassage]:
        """Lấy tất cả passage của một section"""
        return (
            QuestionPassage.query.filter_by(
                section_id=section_id,
                is_visible=True) .order_by(
                QuestionPassage.display_order) .all())

    @staticmethod
    def add_question_to_section(
        section_id: int,
        question_id: int = None,
        question_text: str = None,
        question_type: str = None,
        display_order_in_section: int = None,
        points: float = None,
        passage_id: int = None,
        created_by: int = None,
        sanitize: bool = True,
    ) -> Tuple[bool, str, Optional[Question]]:
        """
        Thêm hoặc liên kết câu hỏi vào section

        Args:
            section_id: ID của section
            question_id: ID của câu hỏi (nếu đã tồn tại)
            question_text: Nội dung câu hỏi (nếu tạo mới)
            question_type: Loại câu hỏi
            display_order_in_section: Thứ tự trong section
            points: Điểm của câu hỏi
            passage_id: ID của passage liên kết
            created_by: User ID tạo câu hỏi
            sanitize: Có sanitize HTML hay không

        Returns:
            Tuple (success: bool, message: str, question: Question or None)
        """
        try:
            # Kiểm tra section tồn tại
            section = QuestionSection.query.get(section_id)
            if not section:
                return False, "Section không tồn tại", None

            # Nếu có question_id, cập nhật câu hỏi hiện tại
            if question_id:
                question = Question.query.get(question_id)
                if not question:
                    return False, "Câu hỏi không tồn tại", None

                question.section_id = section_id

                if display_order_in_section:
                    question.display_order_in_section = display_order_in_section
                else:
                    # Lấy max display_order_in_section
                    last_q = (
                        Question.query.filter_by(section_id=section_id)
                        .order_by(Question.display_order_in_section.desc())
                        .first()
                    )
                    question.display_order_in_section = (
                        (last_q.display_order_in_section + 1) if last_q else 1
                    )

                if passage_id:
                    question.passage_id = passage_id

                db.session.commit()

                return True, "Cập nhật câu hỏi trong section thành công", question

            # Nếu không có question_id, tạo câu hỏi mới
            if not question_text or not question_type:
                return False, "Cần có question_text và question_type", None

            # Sanitize HTML nếu cần
            if sanitize:
                question_text = RichTextService.sanitize_html(question_text)

            # Lấy paper_id từ section
            paper_id = section.paper_id

            # Lấy question_number
            last_q = (
                Question.query.filter_by(paper_id=paper_id)
                .order_by(Question.question_number.desc())
                .first()
            )
            question_number = (last_q.question_number + 1) if last_q else 1

            # Lấy display_order_in_section nếu chưa có
            if display_order_in_section is None:
                last_q_in_section = (
                    Question.query.filter_by(section_id=section_id)
                    .order_by(Question.display_order_in_section.desc())
                    .first()
                )
                display_order_in_section = (
                    (last_q_in_section.display_order_in_section + 1)
                    if last_q_in_section
                    else 1
                )

            # Tạo câu hỏi mới
            question = Question(
                paper_id=paper_id,
                question_number=question_number,
                question_text=question_text,
                question_type=question_type,
                part="reading",  # Mặc định cho section
                section_id=section_id,
                passage_id=passage_id,
                display_order_in_section=display_order_in_section,
                points=points,
                is_rich_text=True,
                created_by=created_by,
                is_visible=True,
            )

            db.session.add(question)
            db.session.commit()

            return True, "Thêm câu hỏi vào section thành công", question

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi thêm câu hỏi vào section: {str(e)}", None

    @staticmethod
    def get_questions_in_section(
        section_id: int, include_hidden: bool = False
    ) -> List[Question]:
        """
        Lấy tất cả câu hỏi trong section

        Args:
            section_id: ID của section
            include_hidden: Có bao gồm câu hỏi ẩn không

        Returns:
            List của Question objects
        """
        query = Question.query.filter_by(section_id=section_id)

        if not include_hidden:
            query = query.filter_by(is_visible=True)

        return query.order_by(Question.display_order_in_section).all()

    @staticmethod
    def get_section_with_questions(section_id: int) -> Dict:
        """
        Lấy section với tất cả câu hỏi và passage

        Args:
            section_id: ID của section

        Returns:
            Dict chứa section info, passages, và questions
        """
        section = QuestionSection.query.get(section_id)

        if not section:
            return None

        passages = ExamSectionService.get_passages_by_section(section_id)
        questions = ExamSectionService.get_questions_in_section(section_id)

        return {
            "section_id": section.section_id,
            "section_name": section.section_name,
            "section_type": (
                section.section_type.section_type_name if section.section_type else None
            ),
            "section_type_key": (
                section.section_type.section_type_key if section.section_type else None
            ),
            "description": section.section_description,
            "display_order": section.display_order,
            "passages": [
                {
                    "passage_id": p.passage_id,
                    "passage_title": p.passage_title,
                    "passage_text": p.passage_text,
                    "author_name": p.author_name,
                    "display_order": p.display_order,
                }
                for p in passages
            ],
            "questions": [
                {
                    "question_id": q.question_id,
                    "question_number": q.question_number,
                    "question_text": q.question_text,
                    "question_type": q.question_type,
                    "points": float(q.points) if q.points else None,
                    "display_order_in_section": q.display_order_in_section,
                    "passage_id": q.passage_id,
                }
                for q in questions
            ],
        }

    @staticmethod
    def reorder_questions_in_section(
        section_id: int, question_orders: List[Dict]
    ) -> Tuple[bool, str]:
        """
        Sắp xếp lại thứ tự câu hỏi trong section

        Args:
            section_id: ID của section
            question_orders: List của {'question_id': int, 'display_order': int}

        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            for order_item in question_orders:
                question = Question.query.get(order_item["question_id"])
                if question and question.section_id == section_id:
                    question.display_order_in_section = order_item["display_order"]

            db.session.commit()

            return True, "Sắp xếp lại thứ tự thành công"

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi sắp xếp lại thứ tự: {str(e)}"
