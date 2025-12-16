using System;
using System.Collections.Generic;
using System.Text;

namespace FormatingLib.Model
{
    public class FormatingConfiguration
    {
        public bool OverrideFormating {  get; set; }
        public bool NormalText { get; set; }
        public bool Headings { get; set; }
        public bool Captions { get; set; }
        public bool PagesNumeration { get; set; }
        public bool PageFields { get; set; }

        public static FormatingConfiguration ReturnDefault()
        {
            FormatingConfiguration configuration = new();
            
            configuration.OverrideFormating = false;
            configuration.NormalText = true;
            configuration.Headings = true;
            configuration.Captions = true;
            configuration.PagesNumeration = true;
            configuration.PageFields = true;

            return configuration;

        }

    }
}
