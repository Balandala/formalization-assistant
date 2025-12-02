using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using Charts = DocumentFormat.OpenXml.Drawing.Charts;
using static FormatingLib.StylesLib;
using DocumentFormat.OpenXml.Vml;

namespace FormatingLib
{
    public class WordProcessor
    {
        public static void ProcessFile(string filepath)
        {
            if (!filepath.EndsWith(".docx"))
                throw new ArgumentException("Invalid file type");
            using (WordprocessingDocument doc = WordprocessingDocument.Open(filepath, true))
            {
                Process(doc);
            }
        }

        public static void Process(WordprocessingDocument doc)
        {
            DocInit(doc);
            //SetSectionProperties(doc);
            OverrideStyles(GetStylesDefinitionPart(doc));
            IEnumerable<Paragraph> paragraphs = doc.MainDocumentPart.Document.Body.Descendants<Paragraph>();
            foreach (var p in paragraphs)
            {
                if (IsTitle(p, paragraphs))
                {
                    ApplyStyleToParagraph(doc, StyleIds.Heading1, p);
                }
                else if (IsAfterMedia(p, paragraphs))
                {
                    ApplyStyleToParagraph(doc, StyleIds.Media, p);
                }
                else if (IsContainsMedia(p))
                {
                    ApplyStyleToParagraph(doc, StyleIds.Heading1, p);
                }
                else
                {
                    ApplyStyleToParagraph(doc, StyleIds.Normal, p);
                }
            }
        }

        private static void DocInit(WordprocessingDocument doc)
        {
            MainDocumentPart mainPart = doc.MainDocumentPart ?? doc.AddMainDocumentPart();
            if (mainPart.Document == null)
            {
                mainPart.Document = new Document();
            }
            if (mainPart.Document.Body == null)
            {
                mainPart.Document.Body = new Body();
            }
        }

        private static void SetSectionProperties(WordprocessingDocument doc) //TODO FIX
        {
            Body body = doc.MainDocumentPart.Document.Body ?? new Body();

            var sectionProperties = new SectionProperties();

            Charts.PageMargins pageMargins = new Charts.PageMargins()
            {
                Left = 1700,
                Right = 850,
                Top = 1133,
                Bottom = 1133
            };

            sectionProperties.Append(pageMargins);
            body.Append(sectionProperties);
        }

        private static bool IsTitle(Paragraph p, IEnumerable<Paragraph> allParagraphs)
        {
            if (p == null) return false;

            int score = 0;

            if (IsContainsMedia(p)) score = -100;

            if (IsAfterPageBreak(p, allParagraphs)) score += 2;

            if (IsTextShort(p)) score += 2;

            if (IsHeadingByStructuralPattern(p)) score += 2;

            if (IsHeadingByPosition(p, allParagraphs)) score += 2;

            if (score > 2) return true;


            return false;
        }


        private static bool IsAfterPageBreak(Paragraph p, IEnumerable<Paragraph> allParagraphs)
        {
            int index = allParagraphs.ToList().IndexOf(p);
            if (index == 0) return false;
            return allParagraphs.ElementAt(index - 1).Descendants<Break>().Any(x => x.Type.Value == BreakValues.Page);
        }

        private static bool IsTextShort(Paragraph paragraph)
        {
            var text = paragraph.InnerText.Trim();
            return text.Length > 0 && text.Length < 200;
        }

        private static bool IsHeadingByStructuralPattern(Paragraph paragraph)
        {
            var text = paragraph.InnerText.Trim();
            if (text == null || text.Length == 0)
            {
                return false;
            }
            bool startsWithNumber = char.IsNumber(text[0]);
            bool isInNumberedList = paragraph.ParagraphProperties?.NumberingProperties?.NumberingId != null;

            return startsWithNumber && !isInNumberedList;
                
        }

        private static bool IsHeadingByPosition(Paragraph p, IEnumerable<Paragraph> allParagraphs)
        {
            int index = allParagraphs.ToList().IndexOf(p);
            if (index == 0) return true;
            if (index > 0)
            {
                var previousText = allParagraphs.ElementAt(index - 1).InnerText.Trim();
                var currentText = p.InnerText.Trim();

                bool previousEndsWithPunctuation = previousText.EndsWith(".") ||
                                                  previousText.EndsWith("!") ||
                                                  previousText.EndsWith("?");
                bool currentEndsWithPunctuation = currentText.EndsWith(".") ||
                                                 currentText.EndsWith("!") ||
                                                 currentText.EndsWith("?");

                return previousEndsWithPunctuation && !currentEndsWithPunctuation;
            }
            return false;
        }

        private static bool IsAfterMedia(Paragraph p, IEnumerable<Paragraph> allParagraphs)
        {
            int index = allParagraphs.ToList().IndexOf(p);
            if (index == 0) return false;
            if (index > 0)
            {
                if (IsContainsMedia(allParagraphs.ElementAt(index - 1)))
                {
                    return p.InnerText.Length < 200;
                }
            }
            return false;
        }

        private static bool IsContainsMedia(Paragraph p)
        {
            return p.Descendants<ImageFile>().Any() ||
                    p.Descendants<Drawing>().Any();
        }



        // Apply a style to a paragraph.
        private static void ApplyStyleToParagraph(WordprocessingDocument doc, StylesLib.StyleIds styleid, Paragraph p)
        {
            if (doc is null)
            {
                throw new ArgumentNullException(nameof(doc));
            }

            // If the paragraph has no ParagraphProperties object, create one.
            if (p.Elements<ParagraphProperties>().Count() == 0)
            {
                p.PrependChild<ParagraphProperties>(new ParagraphProperties());
            }

            // Get the paragraph properties element of the paragraph.
            ParagraphProperties pPr = p.Elements<ParagraphProperties>().First();


            // Get the Styles part for this document.
            StyleDefinitionsPart? part = GetStylesDefinitionPart(doc);

            // Set the style of the paragraph.
            pPr.ParagraphStyleId = new ParagraphStyleId() { Val = styleid.ToString() };
        }

        private static bool IsStyleIdInDocument(WordprocessingDocument doc, string styleid)
        {
            // Get access to the Styles element for this document.
            Styles? s = doc.MainDocumentPart?.StyleDefinitionsPart?.Styles;

            if (s is null)
            {
                return false;
            }

            // Check that there are styles and how many.
            int n = s.Elements<Style>().Count();

            if (n == 0)
            {
                return false;
            }

            // Look for a match on styleid.
            Style? style = s.Elements<Style>()
                .Where(st => (st.StyleId is not null && st.StyleId == styleid) && (st.Type is not null && st.Type == StyleValues.Paragraph))
                .FirstOrDefault();
            if (style is null)
            {
                return false;
            }

            return true;
        }



        private static StyleDefinitionsPart GetStylesDefinitionPart(WordprocessingDocument doc)
        {
            MainDocumentPart mainPart = doc.MainDocumentPart ?? doc.AddMainDocumentPart();
            StyleDefinitionsPart? stylePart = mainPart.StyleDefinitionsPart;
            if (stylePart == null)
            {
                return AddStylesToPackage(doc);
            }
            else
            {
                return stylePart;
            }
        }

        private static StyleDefinitionsPart AddStylesToPackage(WordprocessingDocument doc)
        {
            StyleDefinitionsPart stylePart = doc.MainDocumentPart.AddNewPart<StyleDefinitionsPart>();
            Styles root = new Styles();

            return stylePart;
        }

        private static void OverrideStyles(StyleDefinitionsPart styleDefinitionsPart)
        {
            styleDefinitionsPart.Styles ??= new Styles();
            Styles styles = styleDefinitionsPart.Styles;
            
            styles.Append(MakeTextStyle());
            styles.Append(MakeTitleStyle());
            styles.AppendChild(MakeMediaStyle());

        }



    }
}
