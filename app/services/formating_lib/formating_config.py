class Config:
    def __init__(
            self,
            override_formatting: bool = False,
            normal_text: bool = True,
            headings: bool = True,
            captions: bool = True,
            pages_numerations: bool = True,
            page_fields: bool = True,
            table_of_contents: bool = False,
            table_of_contents_page: int = 2,
    ):
        self.override_formatting = override_formatting
        self.normal_text = normal_text
        self.headings = headings
        self.captions = captions
        self.pages_numerations = pages_numerations
        self.page_fields = page_fields
        self.table_of_contents = table_of_contents
        self.table_of_contents_page = max(1, table_of_contents_page)
