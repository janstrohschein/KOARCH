FROM mcr.microsoft.com/dotnet/core/sdk:3.1 AS build-env
WORKDIR /app/src

COPY . /app
RUN dotnet publish ProtocolTranslationDocker -c Release -o out


FROM mcr.microsoft.com/dotnet/core/aspnet:3.1
COPY . /app
WORKDIR /app/src
COPY --from=build-env /app/src/out .
ENTRYPOINT ["dotnet", "OPCUAGateway.dll"]
