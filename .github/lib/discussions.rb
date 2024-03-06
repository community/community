# frozen_string_literal: true

require "active_support/core_ext/date_and_time/calculations"
require "active_support/core_ext/numeric/time"

Discussion = Struct.new(
  :id,
  :url,
  :title
) do
  def self.all(owner: nil, repo: nil, category: nil)
    return [] if owner.nil? || repo.nil? || category.nil?

    query = <<~QUERY
    {
      repository(owner: "#{owner}", name: "#{repo}"){
        discussions(
          first: 100,
          after: "%ENDCURSOR%"
          #{"answered: false," if category.answerable}
          categoryId: "#{category.id}"
          orderBy: { field: CREATED_AT, direction: ASC }
        ) {
          nodes {
            id
            url
            title
            closed
            locked
            updatedAt
            comments(last: 1) {
              totalCount
              nodes {
                createdAt
              }
            }
            labels(first: 100) {
              nodes {
                name
              }
            }
          }
          pageInfo {
            hasNextPage
            endCursor
          }
        }
      }
    }
    QUERY

    cutoff_date = Time.now.advance(days: -60)
    GitHub.new.post(graphql: query).map! { |r| r.dig('discussions', 'nodes') }
      .flatten
      .reject { |r| Date.parse(r["updatedAt"]).after?(cutoff_date) }
      .select { |r| r.dig("labels", "nodes").map { |l| l["name"] }.include?("Question") }
      .reject { |r| r["closed"] }
      .reject { |r| r["locked"] }
      .reject { |r| r.dig("comments", "totalCount") > 0 && Date.parse(r.dig("comments", "nodes", 0, "createdAt")).after?(cutoff_date) }
      #.reject { |r| r.dig("labels", "nodes").map { |l| l["name"] }.include?("stale") }
      .select { |r| r.dig("labels", "nodes").map { |l| l["name"] }.include?("stale") }
      .map do |c|
        Discussion.new(
          c["id"],
          c["url"],
          c["title"]
        )
      end
  end

  def add_comment(body: nil)
    query = <<~QUERY
    mutation {
      addDiscussionComment(
        input: {
          body: "#{body}",
          discussionId: "#{self.id}",
          clientMutationId: "rubyGraphQL"
        }
      ) {
        clientMutationId
        comment {
           id
           body
        }
      }
    }
    QUERY

    GitHub.new.mutate(graphql: query)
  end

  def add_label(label_id: nil)
    return if label_id.nil?

    query = <<~QUERY
    mutation {
      addLabelsToLabelable(
        input: {
          labelIds: ["#{label_id}"],
          labelableId: "#{self.id}",
          clientMutationId: "rubyGraphQL"
        }
      ) {
        clientMutationId
      }
    }
    QUERY

    GitHub.new.mutate(graphql: query)
  end
end
