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
    )
  end

  def post(graphql:)
    end_cursor = nil
    nodes = []

    loop do
      query = end_cursor.nil? ? graphql.sub(/after.*\n/, "") : graphql.sub("%ENDCURSOR%", end_cursor)

      response = @conn.post("/graphql") do |req|
        req.body = { query: }.to_json
      end

      node = JSON.parse(response.body).dig("data", "repository")
      nodes << node

      break unless node.dig("discussions", "pageInfo", "hasNextPage")

      end_cursor = node.dig("discussions", "pageInfo", "endCursor")
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
