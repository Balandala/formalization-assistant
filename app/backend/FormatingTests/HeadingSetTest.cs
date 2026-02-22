using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using FormatingLib;
using FormatingLib.Model;
using System.Security.Cryptography;

namespace FormatingTests
{
    [TestClass]
    public sealed class HeadingSetTest
    {
        [TestMethod]
        public void TestFindNoLessThan80PercentHeadings()
        {
            // Arrange
            String path = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "../../../resources/");
            WordProcessor wp = new WordProcessor(new FormatingConfiguration());
            string src = "testDoc.docx";
            List<int> paragraphIndexes;
            WordprocessingDocument doc;
            using (WordprocessingDocument reference = WordprocessingDocument.Open(path + src, false))
            {
                paragraphIndexes = GetHeadingParahraphIndexes(reference);
                doc = reference.Clone();
            }

            // Act
            wp.Process(doc);

            // Assert
            int score = 0;
            int maxScore = paragraphIndexes.Count;

            List<Paragraph> paragraphs = GetAllParagraphs(doc);
            foreach (int index in paragraphIndexes)
            {
                Paragraph p = paragraphs[index];
                if (IsParagraphHaveThisStyleName(p, StylesLib.StyleIds.Heading1.ToString()))
                {
                    Console.WriteLine($"Heading '{p.InnerText}' is found");
                    score++;
                }
                else
                {
                    Console.WriteLine($"Heading '{p.InnerText}' is NOT found");
                }
            }

            double percent = (double)score / maxScore * 100;
            int percentToPass = 80;
            Assert.IsGreaterThanOrEqualTo(percentToPass, percent, $"Should no less than 80%. Currently {percent}/100%");

        }


        private List<int> GetHeadingParahraphIndexes(WordprocessingDocument doc)
        {
            List<int> paragraphIndexes = [];
            List<Paragraph> paragraphs = GetAllParagraphs(doc);
            for (int i = 0; i < paragraphs.Count(); i++)
            {
                string? styleName = GetStyleName(paragraphs[i]);
                if (styleName != null && styleName == "H1")
                {
                    paragraphIndexes.Add(i);
                }
            }
            return paragraphIndexes;

        }

        private List<Paragraph> GetAllParagraphs(WordprocessingDocument doc)
        {
            return doc.MainDocumentPart.Document.Body.Descendants<Paragraph>().ToList();
        }

        private string? GetStyleName(Paragraph p)
        {
            ParagraphProperties? paragraphProperties = p.ParagraphProperties;
            if (paragraphProperties is null) return null;
            ParagraphStyleId? paragraphStyleId = paragraphProperties.ParagraphStyleId;
            if (paragraphStyleId is null) return null;
            return paragraphStyleId.Val;
        }

        private bool IsParagraphHaveThisStyleName(Paragraph p, string styleName)
        {
            return styleName == GetStyleName(p);
        }
    }
}
