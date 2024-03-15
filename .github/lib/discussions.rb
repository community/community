# frozen_string_literal: true

require "active_support"
require "active_support/core_ext/date_and_time/calculations"
require "active_support/core_ext/numeric/time"

Discussion = Struct.new(
  :id,
  :url,
  :title,
  :labelled
) do
  def self.all(owner: nil, repo: nil)
    return [] if owner.nil? || repo.nil?

    cutoff_date = Time.now.advance(days: -60).to_date.to_s
    searchquery = "repo:#{owner}/#{repo} is:unanswered is:open is:unlocked updated:<#{cutoff_date} category:Copilot category:Accessibility category:\\\"Projects and Issues\\\" label:Question"

    query = <<~QUERY
    {
      search(
        first: 100
        after: "%ENDCURSOR%"
        query: "#{searchquery}"
        type: DISCUSSION
      ) {
        discussionCount
        ...Results
        pageInfo {
          hasNextPage
          endCursor
        }
      }
      rateLimit {
        limit
        cost
        remaining
        resetAt
      }
    }
    fragment Results on SearchResultItemConnection {
      nodes {
        ... on Discussion {
          id
          url
          title
          labels(first: 10) {
            nodes {
              name
            }
          }
        }
      }
    }
    QUERY

    GitHub.new.post(graphql: query)
      .map! { |r| r.dig('nodes') }
      .flatten
      .map do |c|
        labelled = c.dig("labels", "nodes").map { |l| l["name"] }.include?("inactive")
        Discussion.new(
          c["id"],
          c["url"],
          c["title"],
          labelled
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
