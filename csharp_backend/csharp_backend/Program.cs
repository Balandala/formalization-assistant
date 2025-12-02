using FormatingLib;

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

        WordProcessor.ProcessFile(request.filepath);
        return Results.Ok();
    //}
    //catch (Exception ex)
    //{
    //    return Results.InternalServerError($"Server raised an exception: {ex.Message}");
    //}
}
);

app.Run();

class ProcessRequest
{
    public string filepath {  get; set; }
}
