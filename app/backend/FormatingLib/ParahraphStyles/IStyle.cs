using DocumentFormat.OpenXml.Wordprocessing;
using System;
using System.Collections.Generic;
using System.Text;

namespace FormatingLib.ParagraphStyles
{
    public interface IStyle
    {
        public string Styleid { get; }

        public Style GetStyle();
    }
}
