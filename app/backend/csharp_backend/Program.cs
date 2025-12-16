using FormatingLib;
using FormatingLib.Model;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddOpenApi();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}



app.MapPost("/process", (ProcessRequest request) =>
{
    //try
    //{
        if (string.IsNullOrEmpty(request.filepath))
            return Results.BadRequest("File cannot be empty");


        FormatingConfiguration config;
        if (request.config == null)
        {
            config = FormatingConfiguration.ReturnDefault();
        }
        else
        {
            config = request.config;
        }
        WordProcessor wp = new WordProcessor(config);
        wp.ProcessFile(request.filepath);
        return Results.Ok();
    //}
    //catch (Exception ex)
    //{
    //    return Results.InternalServerError($"Server raised an exception: {ex.Message}");
    //}
});

app.Run();

class ProcessRequest
{
    public string filepath {  get; set; }

    public FormatingConfiguration? config { get; set; }
}
