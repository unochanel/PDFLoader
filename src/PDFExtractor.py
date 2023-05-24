import pdfplumber
import fitz
from typing import List, Dict, Tuple
from lib.json import write_to_json


class PDFExtractor:
    def __init__(
        self,
        pdf_path: str,
        outline_font_size: int = 7,
        ignore_minimum_font_size: int = 7,
    ):
        self.pdf_path = pdf_path
        self.outline_font_size = outline_font_size
        self.ignore_minimum_font_size = ignore_minimum_font_size

    def _extract_text_with_font_size(self) -> List[Dict[str, any]]:
        # pdfを開き、文字の大きさと内容を抽出する
        with pdfplumber.open(self.pdf_path) as pdf:
            return self._extract_text_from_pages(
                pdf.pages, self.ignore_minimum_font_size
            )

    @staticmethod
    def _extract_text_from_pages(pages, ignore_minimum_font_size):
        extracted_pages = []
        for page_num, page in enumerate(pages, start=1):
            page_content = [
                {"size": round(char["size"]), "text": char["text"]}
                for char in page.chars
                if round(char["size"]) >= ignore_minimum_font_size
            ]
            extracted_pages.append({"page_num": page_num, "content": page_content})
        return extracted_pages

    @staticmethod
    def _combine_same_size_text(pages: List[Dict[str, any]]) -> List[Dict[str, any]]:
        # 同じサイズのテキストを結合する
        for page in pages:
            page["content"] = PDFExtractor._combine_text_of_same_size(page["content"])
        return pages

    @staticmethod
    def _combine_text_of_same_size(content):
        combined_content: List[Dict[str, any]] = []
        current_size: int = 0
        current_text: str = ""

        for item in content:
            if current_text and current_size != item["size"]:
                combined_content.append({"size": current_size, "text": current_text})
                current_text = ""
            current_size = item["size"]
            current_text = current_text + item["text"]
        if current_text:
            combined_content.append({"size": current_size, "text": current_text})
        return combined_content

    def _get_outlines(self) -> List[fitz.Outline]:
        doc = fitz.open(self.pdf_path)
        return doc.get_toc()

    def _extract_all_sections(
        self, contents: List[Dict[str, any]], outlines: List[fitz.Outline]
    ) -> List[Tuple[str, str]]:
        sections = []
        for i in range(len(outlines) - 1):
            title, section = self._extract_section_from_content(
                contents, outlines, i, i + 1, self.outline_font_size
            )
            if title and section:
                title = self._create_full_section_title(i, outlines, title)
                sections.append((title, section))
        return sections

    def _extract_section_from_content(
        self,
        contents: List[Dict[str, any]],
        outlines: List[fitz.Outline],
        start_idx: int,
        end_idx: int,
        font_size: int,
    ) -> Tuple[str, str]:
        pagenum, next_pagenum = outlines[start_idx][2], outlines[end_idx][2]
        title, next_title = outlines[start_idx][1], outlines[end_idx][1]
        return self._find_section_in_contents(
            contents, pagenum, next_pagenum, title, next_title, font_size
        )

    @staticmethod
    def _find_section_in_contents(
        contents: List[Dict[str, any]],
        start_page: int,
        end_page: int,
        title: str,
        next_title: str,
        font_size: int,
    ) -> Tuple[str, str]:
        current_title = ""
        current_section = ""
        isFinished = False

        for content in contents[start_page - 1 : end_page]:
            if isFinished:
                break
            for item in content["content"]:
                if item["size"] >= font_size and title in item["text"]:
                    current_title = item["text"]
                elif (
                    current_title
                    and item["size"] >= font_size
                    and next_title in item["text"]
                ):
                    isFinished = True
                    break
                elif current_title:
                    current_section += " " + item["text"]

        return current_title, current_section.strip()

    def _create_full_section_title(
        self, current_index: int, outlines: List[fitz.Outline], title: str
    ) -> str:
        current_top_level = outlines[current_index][0]
        for i in range(current_index, -1, -1):
            if outlines[i][0] < current_top_level:
                title = outlines[i][1] + "_" + title
                current_top_level = outlines[i][0]
        return title

    def call(self):
        extracted_texts = self._extract_text_with_font_size()
        combined_texts = self._combine_same_size_text(extracted_texts)

        pdf_outlines = self._get_outlines()

        sections = self._extract_all_sections(combined_texts, pdf_outlines)
        json_data = [
            {"title": f"{section[0]}", "text": section[1]} for section in sections
        ]
        write_to_json(json_data, "src/resources/output.json")
