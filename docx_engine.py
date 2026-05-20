"""Minimal DOCX generator using only Python stdlib (zipfile + XML)."""
import zipfile, os, io

RELS_XML = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'

WORD_RELS_TEMPLATE = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>{extra}</Relationships>'

CONTENT_TYPES = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Default Extension="jpg" ContentType="image/jpeg"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"

STYLES_XML = f'''<?xml version="1.0" encoding="UTF-8"?>
<w:styles xmlns:w="{W}">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="20"/></w:rPr>
    <w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:pPr><w:spacing w:before="200" w:after="80"/><w:jc w:val="center"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="20"/><w:smallCaps/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:pPr><w:spacing w:before="120" w:after="60"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:i/><w:sz w:val="20"/></w:rPr>
  </w:style>
</w:styles>'''


class DocxWriter:
    def __init__(self):
        self.body_xml = ""
        self.images = {}
        self.img_counter = 0

    def _rpr(self, bold=False, italic=False, size=20, font="Times New Roman", sup=False):
        s = f'<w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/><w:sz w:val="{size}"/>'
        if bold: s += '<w:b/>'
        if italic: s += '<w:i/>'
        if sup: s += '<w:vertAlign w:val="superscript"/>'
        s += '</w:rPr>'
        return s

    def _escape(self, text):
        return text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

    def add_title(self, title, authors, affiliation):
        self.body_xml += f'<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:after="60"/></w:pPr><w:r>{self._rpr(bold=True, size=28)}<w:t>{self._escape(title)}</w:t></w:r></w:p>'
        self.body_xml += f'<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:after="20"/></w:pPr><w:r>{self._rpr(size=22)}<w:t>{self._escape(authors)}</w:t></w:r></w:p>'
        self.body_xml += f'<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:after="120"/></w:pPr><w:r>{self._rpr(italic=True, size=18)}<w:t>{self._escape(affiliation)}</w:t></w:r></w:p>'

    def add_heading(self, text, level=1):
        style = "Heading1" if level == 1 else "Heading2"
        roman = self._to_roman(text) if level == 1 else text
        self.body_xml += f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr><w:r>{self._rpr(bold=True, size=20)}<w:t>{self._escape(roman)}</w:t></w:r></w:p>'

    def _to_roman(self, text):
        return text  # Keep as-is, numbering done in content

    def add_paragraph(self, text, bold=False, italic=False, indent=True, center=False, size=20):
        jc = '<w:jc w:val="center"/>' if center else '<w:jc w:val="both"/>'
        ind = '<w:ind w:firstLine="284"/>' if indent else ''
        self.body_xml += f'<w:p><w:pPr>{jc}{ind}<w:spacing w:after="40" w:line="240" w:lineRule="auto"/></w:pPr><w:r>{self._rpr(bold=bold, italic=italic, size=size)}<w:t xml:space="preserve">{self._escape(text)}</w:t></w:r></w:p>'

    def add_rich_paragraph(self, parts, indent=True, center=False):
        """parts: list of (text, bold, italic, superscript)"""
        jc = '<w:jc w:val="center"/>' if center else '<w:jc w:val="both"/>'
        ind = '<w:ind w:firstLine="284"/>' if indent else ''
        runs = ""
        for part in parts:
            t, b, i = part[0], part[1] if len(part)>1 else False, part[2] if len(part)>2 else False
            sup = part[3] if len(part)>3 else False
            runs += f'<w:r>{self._rpr(bold=b, italic=i, sup=sup)}<w:t xml:space="preserve">{self._escape(t)}</w:t></w:r>'
        self.body_xml += f'<w:p><w:pPr>{jc}{ind}<w:spacing w:after="40" w:line="240" w:lineRule="auto"/></w:pPr>{runs}</w:p>'

    def add_empty_line(self):
        self.body_xml += '<w:p><w:pPr><w:spacing w:after="40"/></w:pPr></w:p>'

    def add_table(self, headers, rows):
        """Add a simple table."""
        ncols = len(headers)
        col_w = 9000 // ncols
        self.body_xml += '<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="9000" w:type="dxa"/><w:tblBorders>'
        for b in ['top','left','bottom','right','insideH','insideV']:
            self.body_xml += f'<w:{b} w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        self.body_xml += '</w:tblBorders></w:tblPr>'
        # Header row
        self.body_xml += '<w:tr>'
        for h in headers:
            self.body_xml += f'<w:tc><w:tcPr><w:tcW w:w="{col_w}" w:type="dxa"/><w:shd w:val="clear" w:fill="D9E2F3"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r>{self._rpr(bold=True, size=16)}<w:t>{self._escape(h)}</w:t></w:r></w:p></w:tc>'
        self.body_xml += '</w:tr>'
        # Data rows
        for row in rows:
            self.body_xml += '<w:tr>'
            for cell in row:
                self.body_xml += f'<w:tc><w:tcPr><w:tcW w:w="{col_w}" w:type="dxa"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r>{self._rpr(size=16)}<w:t>{self._escape(str(cell))}</w:t></w:r></w:p></w:tc>'
            self.body_xml += '</w:tr>'
        self.body_xml += '</w:tbl>'

    def add_caption(self, text):
        self.body_xml += f'<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="40" w:after="80"/></w:pPr><w:r>{self._rpr(bold=False, italic=False, size=16)}<w:t>{self._escape(text)}</w:t></w:r></w:p>'

    def save(self, filepath):
        # Build document.xml
        doc_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W}" xmlns:r="{R}" xmlns:wp="{WP}" xmlns:a="{A}" xmlns:pic="{PIC}">
<w:body>{self.body_xml}
<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="907" w:bottom="1134" w:left="907" w:header="709" w:footer="709"/><w:cols w:num="2" w:space="340"/></w:sectPr>
</w:body></w:document>'''
        
        extra_rels = ""
        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('[Content_Types].xml', CONTENT_TYPES)
            z.writestr('_rels/.rels', RELS_XML)
            z.writestr('word/styles.xml', STYLES_XML)
            z.writestr('word/document.xml', doc_xml)
            z.writestr('word/_rels/document.xml.rels', WORD_RELS_TEMPLATE.format(extra=extra_rels))
        print(f"Saved: {filepath}")
