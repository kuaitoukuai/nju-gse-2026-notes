# -*- coding: utf-8 -*-
"""用 WPS/Word COM 把 docx 导出为 PDF，并报告页数。"""
import os, sys, glob
import win32com.client as win32

OUT = os.path.abspath("dist/print")
pdfdir = os.path.abspath("shots/pdf")
os.makedirs(pdfdir, exist_ok=True)

app = None
for progid in ("KWPS.Application", "Word.Application"):
    try:
        app = win32.Dispatch(progid)
        print("使用", progid)
        break
    except Exception as e:
        print(progid, "不可用:", e)

if app is None:
    sys.exit(1)

try:
    app.Visible = False
    app.DisplayAlerts = 0
except Exception:
    pass

for f in sorted(glob.glob(os.path.join(OUT, "*.docx"))):
    name = os.path.splitext(os.path.basename(f))[0]
    pdf = os.path.join(pdfdir, name + ".pdf")
    try:
        doc = app.Documents.Open(f, ReadOnly=True)
        # 更新域（页码等）
        try:
            doc.Fields.Update()
        except Exception:
            pass
        pages = doc.ComputeStatistics(2)  # wdStatisticPages
        doc.ExportAsFixedFormat(pdf, 17)  # wdExportFormatPDF
        doc.Close(0)
        print(f"{name}: {pages} 页 -> {pdf}")
    except Exception as e:
        print(f"{name} 失败: {e}")

try:
    app.Quit()
except Exception:
    pass
