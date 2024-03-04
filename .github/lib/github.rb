# frozen_string_literal: true

require "faraday"
require "json"

require_relative "./categories"
require_relative "./discussions"

# A class to make it easier to send requests to the GitHub GraphQL endpoint
class GitHub
  def initialize
    @conn = Faraday.new(
      url: "https://api.github.com",
      headers: {
        Authorization: "bearer #{ENV['GITHUB_TOKEN']}"
      }
    ) do |f|
      f.response :raise_error
    end
  end

  def post(graphql:)
    end_cursor = nil
    nodes = []

    loop do
      query = end_cursor.nil? ? graphql.sub(/after.*\n/, "") : graphql.sub("%ENDCURSOR%", end_cursor)

      response = @conn.post("/graphql") do |req|
        req.options.timeout = 10
        req.body = { query: }.to_json
      end

      if rate_limit = JSON.parse(response.body).dig("data", "rateLimit")
        puts "Rate limit: limit - #{rate_limit["limit"]}, cost - #{rate_limit["cost"]}, remaining - #{rate_limit["remaining"]}, resetAt - #{rate_limit["resetAt"]}"
      end

      node = JSON.parse(response.body).dig("data", "repository")
      node = JSON.parse(response.body).dig("data", "search") if node.nil?
      nodes << node

      break unless node&.dig("pageInfo", "hasNextPage")

      end_cursor = node.dig("pageInfo", "endCursor")
    end

    nodes.flatten
  end

  def mutate(graphql:)
    response = @conn.post("/graphql") do |req|
      req.body = { query: graphql }.to_json
    end

    JSON.parse(response.body)
  end
end
