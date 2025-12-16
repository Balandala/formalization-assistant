using DocumentFormat.OpenXml.Wordprocessing;
using System;
using System.Collections.Generic;
using System.Text;

namespace FormatingLib.ParagraphStyles
{
    internal class Normal : IStyle
    {
        public string Styleid => "Normal";
        public Style GetStyle()
        {
            Style style = new Style()
            {
                Type = StyleValues.Paragraph,
                StyleId = this.Styleid,
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
            Bold bold1 = new Bold();
            RunFonts font1 = new RunFonts() { Ascii = "Times New Roman" };
            // Specify a 14 point size.
            FontSize fontSize1 = new FontSize() { Val = "28" };
            styleRunProperties1.Append(font1);
            styleRunProperties1.Append(fontSize1);

            // Add the run properties to the style.
            style.Append(styleRunProperties1);


            return style;
        }
    }
}
