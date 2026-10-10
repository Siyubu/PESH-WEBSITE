const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  HeadingLevel, AlignmentType, PageBreak, Footer, PageNumber,
} = require("docx");

const path = require("path");
const OUT = path.join(__dirname, "..", "exam-documents");
const data = JSON.parse(fs.readFileSync(path.join(__dirname, "exam_docs_data.json"), "utf8"));
const NAMES = { word: "Microsoft Word", excel: "Microsoft Excel", internet: "Internet and AI", scratch: "Scratch Programming" };
const LETTERS = "ABCDEF";
const NAVY = "012D60";
const FONT = "Arial";

const border = { style: BorderStyle.SINGLE, size: 4, color: "BBBBBB" };
const borders = { top: border, bottom: border, left: border, right: border };

function cell(text, width, opts = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    borders,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    shading: opts.head ? { fill: NAVY, type: ShadingType.CLEAR, color: "auto" } : undefined,
    children: [
      new Paragraph({
        children: [new TextRun({ text, bold: !!opts.head || !!opts.bold, color: opts.head ? "FFFFFF" : undefined, size: 20, font: FONT })],
      }),
    ],
  });
}

function build(slug) {
  const ex = data[slug];
  const name = NAMES[slug];
  const kids = [];

  kids.push(new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { after: 60 }, children: [new TextRun({ text: `${name}: Final Exam`, font: FONT, color: NAVY })] }));
  kids.push(new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "PESH online learning. Question bank for teacher review.", italics: true, color: "555555", font: FONT })] }));
  kids.push(new Paragraph({
    spacing: { after: 240 },
    children: [new TextRun({
      text: `On the website each learner gets ${ex.per_attempt} questions drawn at random from this bank of ${ex.questions.length}, with the answer order shuffled. They have ${ex.minutes} minutes, need ${ex.pass_percent}% to pass, and may retake the exam as many times as they like. Correct answers are never shown to learners. The answer key is on the last pages of this document.`,
      font: FONT, size: 22,
    })],
  }));

  kids.push(new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 160 }, children: [new TextRun({ text: "Questions", font: FONT, color: NAVY })] }));
  ex.questions.forEach((q, i) => {
    kids.push(new Paragraph({ keepNext: true, keepLines: true, spacing: { before: 160, after: 60 }, children: [new TextRun({ text: `${i + 1}. ${q.text}`, bold: true, font: FONT, size: 22 })] }));
    q.options.forEach((o, j) => {
      kids.push(new Paragraph({
        keepNext: j < q.options.length - 1, keepLines: true,
        indent: { left: 720, hanging: 540 }, spacing: { after: 30 },
        children: [new TextRun({ text: `${LETTERS[j]}.\t${o}`, font: FONT, size: 22 })],
        tabStops: [{ type: "left", position: 720 }],
      }));
    });
  });

  kids.push(new Paragraph({ children: [new PageBreak()] }));
  kids.push(new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { after: 100 }, children: [new TextRun({ text: "Answer key (teachers only)", font: FONT, color: NAVY })] }));
  kids.push(new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: "Please check every answer against what you teach. Answers were written from the lesson documents. Edit questions on the website under Admin > Exams.", font: FONT, size: 20, color: "555555" })] }));

  const W = [640, 800, 3500, 4086]; // sums to 9026
  const rows = [new TableRow({ tableHeader: true, children: [cell("No.", W[0], { head: true }), cell("Answer", W[1], { head: true }), cell("Correct answer", W[2], { head: true }), cell("Why", W[3], { head: true })] })];
  ex.questions.forEach((q, i) => {
    rows.push(new TableRow({
      cantSplit: true,
      children: [cell(String(i + 1), W[0]), cell(LETTERS[q.correct], W[1], { bold: true }), cell(q.options[q.correct], W[2]), cell(q.why, W[3])],
    }));
  });
  kids.push(new Table({ width: { size: 9026, type: WidthType.DXA }, columnWidths: W, rows }));

  return new Document({
    creator: "PESH",
    title: `${name} Final Exam`,
    styles: {
      default: { document: { run: { font: FONT, size: 22 } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 40, bold: true, font: FONT }, paragraph: { spacing: { before: 120, after: 120 }, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 30, bold: true, font: FONT }, paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 1 } },
      ],
    },
    sections: [{
      properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
      footers: {
        default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: `PESH  |  ${name} final exam  |  Page `, size: 18, color: "777777", font: FONT }), new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "777777", font: FONT })] })] }),
      },
      children: kids,
    }],
  });
}

(async () => {
  for (const slug of Object.keys(NAMES)) {
    const buf = await Packer.toBuffer(build(slug));
    const file = `${OUT}/PESH ${NAMES[slug]} - Final Exam Questions.docx`;
    fs.writeFileSync(file, buf);
    console.log("wrote", file, buf.length);
  }
})();
