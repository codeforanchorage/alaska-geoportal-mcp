# Friendly landing page for GET / -- what a human sees when they paste the
# server's hostname into a browser, or paste the URL into claude.ai without
# the /mcp path. Served by an API Gateway MOCK integration: no Lambda
# invocation, so scanner traffic to the root (dozens of hits per hour on a
# fresh public hostname) costs nothing, and the WAF still fronts it.
#
# The page is plain HTML with no scripts or external assets. Velocity is
# the template language here, so the body deliberately contains no `$` or
# `#` characters.

locals {
  landing_html = <<-HTML
    <!doctype html>
    <html lang="en">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Alaska Geoportal MCP</title>
    <style>
      body { font: 16px/1.5 system-ui, sans-serif; max-width: 42rem; margin: 3rem auto; padding: 0 1rem; color: #222; }
      code { background: #f2f2f2; padding: .1rem .3rem; border-radius: 3px; }
      h1 { font-size: 1.6rem; }
    </style>
    </head>
    <body>
    <h1>Alaska Geoportal MCP</h1>
    <p>This is a <a href="https://modelcontextprotocol.io/">Model Context Protocol</a> server over the
    <a href="https://gis.data.alaska.gov/">State of Alaska Geoportal</a>: statewide GIS layers published by
    the Alaska Geospatial Office and the Department of Natural Resources. It is read-only and has no
    web interface of its own.</p>
    <p>To use it, add it to an MCP client. In Claude: Settings, Connectors, Add custom connector, and paste
    this URL (the <code>/mcp</code> path is required):</p>
    <p><code>https://alaska-geoportal.codeforanchorage.org/mcp</code></p>
    <p>Then ask questions such as "how many miles of forestry road are in the Mat-Su Borough" or
    "which fire service area is Fairbanks in". The server answers from the official layers and states
    the caveats each layer carries.</p>
    <p>Source, documentation and issues:
    <a href="https://github.com/codeforanchorage/alaska-geoportal-mcp">github.com/codeforanchorage/alaska-geoportal-mcp</a>.
    Run by <a href="https://codeforanchorage.org/">Code for Anchorage</a>. Data is the State of Alaska's;
    check each layer's terms of use.</p>
    </body>
    </html>
  HTML
}

resource "aws_api_gateway_method" "root_get" {
  rest_api_id   = aws_api_gateway_rest_api.mcp_api.id
  resource_id   = aws_api_gateway_rest_api.mcp_api.root_resource_id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "root_get" {
  rest_api_id = aws_api_gateway_rest_api.mcp_api.id
  resource_id = aws_api_gateway_rest_api.mcp_api.root_resource_id
  http_method = aws_api_gateway_method.root_get.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "root_get_200" {
  rest_api_id = aws_api_gateway_rest_api.mcp_api.id
  resource_id = aws_api_gateway_rest_api.mcp_api.root_resource_id
  http_method = aws_api_gateway_method.root_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Content-Type"  = true
    "method.response.header.Cache-Control" = true
  }

  response_models = {
    "text/html" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "root_get_200" {
  rest_api_id = aws_api_gateway_rest_api.mcp_api.id
  resource_id = aws_api_gateway_rest_api.mcp_api.root_resource_id
  http_method = aws_api_gateway_method.root_get.http_method
  status_code = aws_api_gateway_method_response.root_get_200.status_code

  response_parameters = {
    "method.response.header.Content-Type"  = "'text/html; charset=utf-8'"
    "method.response.header.Cache-Control" = "'public, max-age=3600'"
  }

  response_templates = {
    "application/json" = local.landing_html
  }

  depends_on = [aws_api_gateway_integration.root_get]
}
