import {
  Document,
  Packer,
  Paragraph,
  Table,
  TableRow,
  TableCell,
  TextRun,
  AlignmentType,
  BorderStyle,
  WidthType,
  ShadingType,
} from "docx";
import saveAs from "file-saver";
import { TestLedgerItem } from "@/lib/api/types";

/**
 * Generates an official MoSPI / NSSTA Competency Evaluation Report .docx file
 * precisely matching the 4-section format specified in the MoSPI template.
 */
export async function generateTestReportDocx(item: TestLedgerItem): Promise<void> {
  const tableBorders = {
    top: { style: BorderStyle.SINGLE, size: 4, color: "CBD5E1" },
    bottom: { style: BorderStyle.SINGLE, size: 4, color: "CBD5E1" },
    left: { style: BorderStyle.SINGLE, size: 4, color: "CBD5E1" },
    right: { style: BorderStyle.SINGLE, size: 4, color: "CBD5E1" },
    insideHorizontal: { style: BorderStyle.SINGLE, size: 4, color: "E2E8F0" },
    insideVertical: { style: BorderStyle.SINGLE, size: 4, color: "E2E8F0" },
  };

  const createCell = (text: string, isHeader = false, widthPct = 50, bold = false, color = "1E293B") => {
    return new TableCell({
      width: { size: widthPct, type: WidthType.PERCENTAGE },
      shading: isHeader ? { fill: "F1F5F9", type: ShadingType.CLEAR } : undefined,
      margins: { top: 120, bottom: 120, left: 180, right: 180 },
      children: [
        new Paragraph({
          children: [
            new TextRun({
              text: text || "N/A",
              bold: isHeader || bold,
              color: isHeader ? "0F172A" : color,
              size: 20, // 10pt
              font: "Calibri",
            }),
          ],
        }),
      ],
    });
  };

  // Section I: Officer Profile Table
  const section1Rows = [
    ["Candidate Full Name", item.full_name],
    ["Official Email", item.email],
    ["Cadre / Role", item.role_name],
    ["Designation", item.designation],
    ["Department / Unit", item.department],
    ["Evaluation Session ID", item.session_id],
    ["Date & Time of Test", item.timestamp],
  ].map(([label, val]) =>
    new TableRow({
      children: [
        createCell(label, true, 35),
        createCell(val || "N/A", false, 65, false, "0F172A"),
      ],
    })
  );

  // Section II: Performance & Scores Table
  const section2aRows = [
    ["Test Report Number", item.report_id],
    ["Competency Module", item.competency_name],
    ["Evaluation Tier / Difficulty", item.tier],
    ["Difficulty Band (Bloom Level)", item.difficulty_band],
    ["Assessment Score", `${item.score}%`],
    ["Correct / Total Questions", `${item.correct_count} / ${item.total_questions}`],
    ["Passing Score Benchmark", `${item.passing_score}%`],
    ["Result Status", item.result_status],
    ["Next Tier Unlocked", item.next_tier_unlocked || "None / Maximum Tier Achieved"],
  ].map(([label, val]) =>
    new TableRow({
      children: [
        createCell(label, true, 35),
        createCell(
          val,
          false,
          65,
          label === "Result Status" || label === "Assessment Score",
          label === "Result Status" && item.result_status === "PASSED"
            ? "047857"
            : label === "Result Status"
            ? "B91C1C"
            : "0F172A"
        ),
      ],
    })
  );

  // Section II-B: KPI Index Table
  const section2bRows = [
    [
      "Competency Mastery Index",
      item.mastery !== null ? `${(item.mastery * 100).toFixed(1)}% (BKT / IRT Calibrated)` : "Unassessed",
    ],
    [
      "Estimation Certainty (Confidence)",
      `${(item.confidence * 100).toFixed(0)}% Certainty`,
    ],
    [
      "Sub-Skill Coverage Ratio",
      `${(item.coverage * 100).toFixed(0)}% Curriculum Coverage`,
    ],
    [
      "Uncertainty Level",
      (item.uncertainty ?? 0.15).toFixed(2),
    ],
    [
      "Cumulative Evidence Count",
      `${item.evidence_count} recorded evidence item(s)`,
    ],
    [
      "Evidence Diversity (Distinct Types)",
      `${item.evidence_diversity} distinct modalities`,
    ],
    [
      "Competencies Assessed (to date / required)",
      item.assessed_count,
    ],
  ].map(([label, val]) =>
    new TableRow({
      children: [
        createCell(label, true, 35),
        createCell(val, false, 65, false, "0F172A"),
      ],
    })
  );

  // Section III: Audit Trail & Lineage Table
  const section3Rows = [
    ["Evidence Type", item.evidence_type],
    ["Reliability Status", item.reliability_status],
    ["Content Lineage (Provenance)", item.provenance],
    ["Cognitive Evidence Weight", item.weight.toFixed(1)],
  ].map(([label, val]) =>
    new TableRow({
      children: [
        createCell(label, true, 35),
        createCell(val, false, 65, false, "0F172A"),
      ],
    })
  );

  // Section IV: Questions Matrix Table
  const qItems = item.items || [];
  const qHeaderRow = new TableRow({
    children: [
      createCell("Q. No.", true, 8, true),
      createCell("Sub-Skill", true, 22, true),
      createCell("Question Text", true, 40, true),
      createCell("Selected", true, 10, true),
      createCell("Correct", true, 10, true),
      createCell("Result", true, 10, true),
    ],
  });

  const qRows = qItems.map((q, idx) => {
    return new TableRow({
      children: [
        createCell(`Q${idx + 1}`, false, 8, true),
        createCell(q.subskill_name || "Statistical Methodology", false, 22),
        createCell(q.question_text || "Diagnostic test item prompt", false, 40),
        createCell(q.user_selected, false, 10),
        createCell(q.correct_option, false, 10),
        createCell(
          q.is_correct ? "PASS (Y)" : "FAIL (N)",
          false,
          10,
          true,
          q.is_correct ? "047857" : "B91C1C"
        ),
      ],
    });
  });

  // Section IV-B: Misconception & Remediation Notes for Incorrect Answers
  const incorrectItems = qItems.filter((q) => !q.is_correct);
  const misconceptionRows =
    incorrectItems.length > 0
      ? incorrectItems.map((q, idx) =>
          new TableRow({
            children: [
              createCell(`${q.question_number || `Q${idx + 1}`} — Misconception & Remediation`, true, 35),
              createCell(
                `[Error Identified]: ${q.misconception_hint || "Candidate selected non-standard formulation."}\n[Remediation Plan]: ${q.remediation_steps || "Consult official MoSPI NSSTA handbook."}`,
                false,
                65,
                false,
                "991B1B"
              ),
            ],
          })
        )
      : [
          new TableRow({
            children: [
              createCell("Diagnostic Summary", true, 35),
              createCell("All questions answered correctly. Zero conceptual misconceptions detected.", false, 65, false, "047857"),
            ],
          }),
        ];

  const doc = new Document({
    sections: [
      {
        properties: {
          page: {
            margin: { top: 1000, bottom: 1000, left: 1200, right: 1200 },
          },
        },
        children: [
          // Header
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({
                text: "GOVERNMENT OF INDIA",
                bold: true,
                size: 26,
                font: "Calibri",
                color: "0F172A",
              }),
            ],
          }),
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({
                text: "Ministry of Statistics and Programme Implementation (MoSPI)",
                size: 22,
                font: "Calibri",
                color: "334155",
              }),
            ],
          }),
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({
                text: "National Statistical Systems Training Academy (NSSTA)",
                size: 20,
                font: "Calibri",
                color: "475569",
              }),
            ],
          }),
          new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { before: 200, after: 300 },
            children: [
              new TextRun({
                text: "INDIVIDUAL COMPETENCY DIAGNOSTIC & TEST EVALUATION REPORT",
                bold: true,
                size: 24,
                font: "Calibri",
                color: "1E3A8A",
              }),
            ],
          }),

          // SECTION I
          new Paragraph({
            spacing: { before: 200, after: 120 },
            children: [
              new TextRun({
                text: "SECTION I: OFFICER PROFILE & ADMINISTRATIVE DETAILS",
                bold: true,
                size: 20,
                color: "0F172A",
              }),
            ],
          }),
          new Table({
            borders: tableBorders,
            width: { size: 100, type: WidthType.PERCENTAGE },
            rows: section1Rows,
          }),

          // SECTION II
          new Paragraph({
            spacing: { before: 300, after: 120 },
            children: [
              new TextRun({
                text: "SECTION II: EXECUTIVE PERFORMANCE & KPI SUMMARY",
                bold: true,
                size: 20,
                color: "0F172A",
              }),
            ],
          }),
          new Paragraph({
            spacing: { before: 80, after: 80 },
            children: [
              new TextRun({
                text: "Test & Score Details",
                bold: true,
                italics: true,
                size: 18,
                color: "334155",
              }),
            ],
          }),
          new Table({
            borders: tableBorders,
            width: { size: 100, type: WidthType.PERCENTAGE },
            rows: section2aRows,
          }),

          new Paragraph({
            spacing: { before: 200, after: 80 },
            children: [
              new TextRun({
                text: "KPI Index (Bayesian / IRT Calibrated Metrics)",
                bold: true,
                italics: true,
                size: 18,
                color: "334155",
              }),
            ],
          }),
          new Table({
            borders: tableBorders,
            width: { size: 100, type: WidthType.PERCENTAGE },
            rows: section2bRows,
          }),

          // SECTION III
          new Paragraph({
            spacing: { before: 300, after: 120 },
            children: [
              new TextRun({
                text: "SECTION III: AUDIT TRAIL, PROVENANCE & RELIABILITY",
                bold: true,
                size: 20,
                color: "0F172A",
              }),
            ],
          }),
          new Table({
            borders: tableBorders,
            width: { size: 100, type: WidthType.PERCENTAGE },
            rows: section3Rows,
          }),

          // SECTION IV
          new Paragraph({
            spacing: { before: 300, after: 120 },
            children: [
              new TextRun({
                text: "SECTION IV: DIAGNOSTIC QUESTION-BY-QUESTION ANALYSIS",
                bold: true,
                size: 20,
                color: "0F172A",
              }),
            ],
          }),
          new Table({
            borders: tableBorders,
            width: { size: 100, type: WidthType.PERCENTAGE },
            rows: [qHeaderRow, ...qRows],
          }),

          new Paragraph({
            spacing: { before: 200, after: 80 },
            children: [
              new TextRun({
                text: "Misconception & Remediation Notes",
                bold: true,
                italics: true,
                size: 18,
                color: "334155",
              }),
            ],
          }),
          new Table({
            borders: tableBorders,
            width: { size: 100, type: WidthType.PERCENTAGE },
            rows: misconceptionRows,
          }),
        ],
      },
    ],
  });

  const blob = await Packer.toBlob(doc);
  const cleanName = item.full_name.replace(/[^a-zA-Z0-9]/g, "_");
  const fileName = `GyanSetu_Test_Report_${item.report_id.replace(/[^a-zA-Z0-9]/g, "_")}_${cleanName}.docx`;
  saveAs(blob, fileName);
}
