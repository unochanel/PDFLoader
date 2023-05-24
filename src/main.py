from PDFExtractor import PDFExtractor


def main():
    pdf_path = "src/resources/t3.pdf"
    pdf_extractor = PDFExtractor(pdf_path)
    pdf_extractor.call()


main()
