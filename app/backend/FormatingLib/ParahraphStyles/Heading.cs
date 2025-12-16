using DocumentFormat.OpenXml.Drawing.Wordprocessing;
using DocumentFormat.OpenXml.Vml.Spreadsheet;
using DocumentFormat.OpenXml.Wordprocessing;
using System;
using System.Collections.Generic;
using System.Text;

namespace FormatingLib.ParagraphStyles
{
    public class Heading : IStyle
    {
        public string Styleid => "Heading1";

        public Style GetStyle()
        {
            Style style = new Style()
            {
                Type = StyleValues.Paragraph,
                StyleId = this.Styleid,
                CustomStyle = true,
                Default = true
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
            RunFonts font1 = new RunFonts() { Ascii = "Times New Roman" };
            FontSize fontSize1 = new FontSize() { Val = "28" };
            styleRunProperties1.Append(font1);
            styleRunProperties1.Append(fontSize1);
            styleRunProperties1.Append(bold1);

            style.Append(styleRunProperties1);


            return style;
        }
    }
}
