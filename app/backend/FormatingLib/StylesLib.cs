using DocumentFormat.OpenXml.Drawing.Wordprocessing;
using DocumentFormat.OpenXml.Vml.Spreadsheet;
using DocumentFormat.OpenXml.Wordprocessing;
using System;
using System.Collections.Generic;
using System.Text;

namespace FormatingLib
{
    public static class StylesLib
    {
        public enum StyleIds
        {
            Normal,
            Heading1,
            Media,
        }
        public static Style MakeTextStyle()
        {
            // Create a new paragraph style and specify some of the properties.
            Style style = new Style()
            {
                Type = StyleValues.Paragraph,
                StyleId = "Normal",
                CustomStyle = true,
                Default = true
            };
            StyleName styleName1 = new StyleName() { Val = "Normal" };
            BasedOn basedOn1 = new BasedOn() { Val = "Normal" };
            NextParagraphStyle nextParagraphStyle1 = new NextParagraphStyle() { Val = "Normal" };
            style.Append(styleName1);
            style.Append(basedOn1);
            style.Append(nextParagraphStyle1);

            StyleParagraphProperties styleParagraphProperties = new StyleParagraphProperties();
            Indentation indentation = new Indentation() { FirstLine = "708" };
            styleParagraphProperties.Append(indentation);
            style.Append(styleParagraphProperties);



            // Create the StyleRunProperties object and specify some of the run properties.
            StyleRunProperties styleRunProperties1 = new StyleRunProperties();
            RunFonts font1 = new RunFonts() { Ascii = "Times New Roman", HighAnsi = "Times New Roman", ComplexScript = "Times New Roman" };
            // Specify a 14 point size.
            FontSize fontSize1 = new FontSize() { Val = "28" };
            styleRunProperties1.Append(font1);
            styleRunProperties1.Append(fontSize1);

            style.Append(styleRunProperties1);

            return style;
        }
        public static Style MakeHeadingStyle()
        {
            Style style = new Style()
            {
                Type = StyleValues.Paragraph,
                StyleId = "Heading1",
                CustomStyle = true,
                Default = false
            };
            StyleName styleName1 = new StyleName() { Val = "Heading1" };
            BasedOn basedOn1 = new BasedOn() { Val = "Heading1" };
            NextParagraphStyle nextParagraphStyle1 = new NextParagraphStyle() { Val = "Normal" };
            style.Append(styleName1);
            style.Append(basedOn1);
            style.Append(nextParagraphStyle1);

            StyleParagraphProperties styleParagraphProperties = new StyleParagraphProperties();
            Justification justification = new Justification { Val = JustificationValues.Center };
            styleParagraphProperties.Append(justification);
            style.Append(styleParagraphProperties);



            StyleRunProperties styleRunProperties1 = new StyleRunProperties();
            Bold bold1 = new Bold();
            RunFonts font1 = new RunFonts() { Ascii = "Times New Roman", HighAnsi = "Times New Roman", ComplexScript = "Times New Roman" };
            FontSize fontSize1 = new FontSize() { Val = "28" };
            styleRunProperties1.Append(font1);
            styleRunProperties1.Append(fontSize1);
            styleRunProperties1.Append(bold1);

            style.Append(styleRunProperties1);


            return style;
        }

        public static Style MakeCaptionStyle()
        {
            Style style = new Style()
            {
                Type = StyleValues.Paragraph,
                StyleId = "Media",
                CustomStyle = true,
                Default = false
            };
            StyleName styleName1 = new StyleName() { Val = "Media" };
            BasedOn basedOn1 = new BasedOn() { Val = "Normal" };
            NextParagraphStyle nextParagraphStyle1 = new NextParagraphStyle() { Val = "Normal" };
            style.Append(styleName1);
            style.Append(basedOn1);
            style.Append(nextParagraphStyle1);

            StyleParagraphProperties styleParagraphProperties = new StyleParagraphProperties();
            Justification justification = new Justification { Val = JustificationValues.Center };
            styleParagraphProperties.Append(justification);
            style.Append(styleParagraphProperties);



            StyleRunProperties styleRunProperties1 = new StyleRunProperties();
            Italic italic1 = new Italic();
            RunFonts font1 = new RunFonts() { Ascii = "Times New Roman", HighAnsi = "Times New Roman", ComplexScript = "Times New Roman" };
            FontSize fontSize1 = new FontSize() { Val = "28" };
            styleRunProperties1.Append(font1);
            styleRunProperties1.Append(fontSize1);
            styleRunProperties1.Append(italic1);

            style.Append(styleRunProperties1);


            return style;
        }
    }
    
}
