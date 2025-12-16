using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using Charts = DocumentFormat.OpenXml.Drawing.Charts;
using static FormatingLib.StylesLib;
using DocumentFormat.OpenXml.Vml;
using FormatingLib.Model;
using DocumentFormat.OpenXml;


namespace FormatingLib
{
    public class WordProcessor
    {
        private FormatingConfiguration config;
        public WordProcessor(FormatingConfiguration config) {
            this.config = config;
        }

        public void ProcessFile(string filepath)
        {
            if (!filepath.EndsWith(".docx"))
                throw new ArgumentException("Invalid file type");
            using (WordprocessingDocument doc = WordprocessingDocument.Open(filepath, true))
            {
                Process(doc);
            }
        }

        public void Process(WordprocessingDocument doc)
        {
            DocInit(doc);
            OverrideStyles(GetStylesDefinitionPart(doc));
            IEnumerable<Paragraph> paragraphs = doc.MainDocumentPart.Document.Body.Descendants<Paragraph>();
            foreach (var p in paragraphs)
            {
                if (config.OverrideFormating)
                {
                    OverrideRunProperties(p);
                }

                if (IsTitle(p, paragraphs) && config.Headings)
                {
                    ApplyStyleToParagraph(doc, StyleIds.Heading1, p);
                }
                else if (IsAfterMedia(p, paragraphs) && config.Captions)
                {
                    ApplyStyleToParagraph(doc, StyleIds.Media, p);
                }
                else if (IsContainsMedia(p))
                {
                    ApplyStyleToParagraph(doc, StyleIds.Heading1, p);
                }
                else if (config.NormalText)
                {
                    ApplyStyleToParagraph(doc, StyleIds.Normal, p);
                }
            }

            if (config.PagesNumeration)
                AddFooter(doc);
            if (config.PageFields)
                AddPageFields(doc);
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

        private static bool IsTitle(Paragraph p, IEnumerable<Paragraph> allParagraphs)
        {
            if (p == null) return false;

            int score = 0;

            if (IsContainsMedia(p) || (IsInTable(p))) score = -100;

            if (IsAfterPageBreak(p, allParagraphs)) score += 2;

            if (IsTextShort(p)) score += 2;

            if (IsHeadingByStructuralPattern(p)) score += 2;

            if (IsHeadingByPosition(p, allParagraphs)) score += 2;

            if (score > 2) return true;


            return false;
        }


        private static bool IsInTable(Paragraph p)
        {
            bool hasTableAncestor = p.Ancestors<Table>().Any();
            bool hasTableCellAncestor = p.Ancestors<TableCell>().Any();

            return hasTableAncestor || hasTableCellAncestor;
        }

        private static bool IsAfterPageBreak(Paragraph p, IEnumerable<Paragraph> allParagraphs)
        {
            int index = allParagraphs.ToList().IndexOf(p);
            if (index == 0) return false;

            bool isAfterPageBreak = allParagraphs.ElementAt(index - 1).Descendants<Break>().Any(x => {
                if (x.Type == null)
                    return false;
                return x.Type.Value == BreakValues.Page;
            });

            return isAfterPageBreak;
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
            styles.Append(MakeHeadingStyle());
            styles.AppendChild(MakeCaptionStyle());

        }

        private Footer MakeFooter()
        {
            Footer footer = new Footer();

            Paragraph paragraph = new Paragraph();

            ParagraphProperties paragraphProperties = new ParagraphProperties();
            paragraphProperties.Append(new Justification()
            {
                Val = JustificationValues.Center
            });
            paragraphProperties.Append(new Indentation()
            {
                Left = "0", 
                Right = "0",     
                FirstLine = "0", 
                Hanging = "0"    
            });
            paragraph.Append(paragraphProperties);

            Run run = new Run();

            RunProperties runProperties = new RunProperties();
            run.Append(runProperties);

            run.Append(new SimpleField()
            {
                Instruction = "PAGE" // Выставление номера страницы
            });

            paragraph.Append(run);
            footer.Append(paragraph);

            return footer;
        }

        private FooterPart GetFooterPart(WordprocessingDocument doc)
        {
            MainDocumentPart mainPart = doc.MainDocumentPart;

            if (mainPart.FooterParts == null || !mainPart.FooterParts.Any())
            {
                return mainPart.AddNewPart<FooterPart>();
            }
            else
            {
                return mainPart.FooterParts.First();
            }
        }

        private SectionProperties GetSectionProperties(WordprocessingDocument doc)
        {
            MainDocumentPart mainPart = doc.MainDocumentPart;
            SectionProperties sectionProps;

            if (mainPart.Document.Body.Elements<SectionProperties>().Any())
            {
                sectionProps = mainPart.Document.Body.Elements<SectionProperties>().Last();
            }
            else
            {
                sectionProps = new SectionProperties();
                mainPart.Document.Body.Append(sectionProps);
            }

            return sectionProps;
        }

        private void AddPageFields(WordprocessingDocument doc)
        {
            Body body = doc.MainDocumentPart.Document.Body;

            var sectionProperties = GetSectionProperties(doc);

            PageMargin pageMargins = new()
            {
                Left = 1700,
                Right = 850,
                Top = 1133,
                Bottom = 1133
            };

            AddOrUpdateElement<PageMargin>(sectionProperties, pageMargins);
        }

        private void AddFooter(WordprocessingDocument doc)
        {
            MainDocumentPart mainPart = doc.MainDocumentPart;

            FooterPart footerPart = GetFooterPart(doc);
            Footer footer = MakeFooter();

            footerPart.Footer = footer;

            SectionProperties sectionProps = GetSectionProperties(doc);

            string footerPartId = mainPart.GetIdOfPart(footerPart);
            FooterReference footerReference = new FooterReference()
            {
                Type = HeaderFooterValues.Default,
                Id = footerPartId
            };

            AddOrUpdateElement<FooterReference>(sectionProps, footerReference);
        }

        private void AddOrUpdateElement<T>(SectionProperties sectionProp, T element)
            where T : OpenXmlElement
        {

            var exisitngElement = sectionProp.Elements<T>().FirstOrDefault();

            if (exisitngElement != null)
            {
                exisitngElement.Remove();
                sectionProp.Append(element);
            }
            else
            {
                sectionProp.Append(element);
            }
        }

        private void OverrideRunProperties(Paragraph p)
        {
            var rPr = p.Descendants<RunProperties>().ToArray();
            foreach (RunProperties prop in rPr) 
            {
                prop.Bold = null;
                prop.Italic = null;
                prop.Underline = null;

                prop.Color = null;
            }
        }
    }

}
