using DocumentFormat.OpenXml.Wordprocessing;
using System;
using System.Collections.Generic;
using System.Text;

namespace FormatingLib.ParagraphStyles
{
    internal class Caption : IStyle
    {
        public string Styleid => "Caption";

        public Style GetStyle()
        {
            Style style = new Style()
            {
                Type = StyleValues.Paragraph,
                StyleId = this.Styleid,
                CustomStyle = true,
                Default = true
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
            RunFonts font1 = new RunFonts() { Ascii = "Times New Roman" };
            FontSize fontSize1 = new FontSize() { Val = "28" };
            styleRunProperties1.Append(font1);
            styleRunProperties1.Append(fontSize1);
            styleRunProperties1.Append(italic1);

            style.Append(styleRunProperties1);


            return style;
        }
    }
}
