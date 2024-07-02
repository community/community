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
    searchquery = "repo:#{owner}/#{repo} is:unanswered is:open is:unlocked updated:<#{cutoff_date} category:Copilot category:Accessibility category:\\\"Projects and Issues\\\" category:Sponsors category:Actions category:\\\"API and Webhooks\\\" category:\\\"Code Search and Navigation\\\" category:\\\"Code Security\\\" category:Codespaces category:Discussions category:Feed category:Lists category:Mobile category:npm category:Packages category:Pages category:Profile category:\\\"Pull Requests\\\" category:Repositories label:Question"

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

  def self.to_be_closed(owner: nil, repo: nil)
    return [] if owner.nil? || repo.nil?

    cutoff_date = Time.now.advance(days: -30).to_date.to_s
    searchquery = "repo:#{owner}/#{repo} is:unanswered is:open is:unlocked updated:<#{cutoff_date} category:Copilot category:Accessibility category:\\\"Projects and Issues\\\" category:Sponsors category:Actions category:\\\"API and Webhooks\\\" category:\\\"Code Search and Navigation\\\" category:\\\"Code Security\\\" category:Codespaces category:Discussions category:Feed category:Lists category:Mobile category:npm category:Packages category:Pages category:Profile category:\\\"Pull Requests\\\" category:Repositories label:Question label:inactive"

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
          comments(last:1) {
            nodes {
              author {
                login
              }
            }
          }
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
      .select { |c| c.dig("comments", "nodes", 0, "author", "login") == "github-actions" }
      .map do |c|
        Discussion.new(
          c["id"],
          c["url"],
          c["title"],
        )
      end
  end

  def self.to_remove_label(owner: nil, repo: nil)
    return [] if owner.nil? || repo.nil?

    searchquery = "repo:#{owner}/#{repo} is:unanswered is:open category:Copilot category:Accessibility category:\\\"Projects and Issues\\\" category:Sponsors category:Actions category:\\\"API and Webhooks\\\" category:\\\"Code Search and Navigation\\\" category:\\\"Code Security\\\" category:Codespaces category:Discussions category:Feed category:Lists category:Mobile category:npm category:Packages category:Pages category:Profile category:\\\"Pull Requests\\\" category:Repositories label:Question label:inactive"

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
          comments(last:1) {
            nodes {
              author {
                login
              }
            }
          }
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
      .reject { |c| c.dig("comments", "nodes", 0, "author", "login") == "github-actions" }
      .map do |c|
        Discussion.new(
          c["id"],
          c["url"],
          c["title"],
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

  def self.remove_label(node_id: nil, label_id: nil)
    return if node_id.nil?
    return if label_id.nil?

    query = <<~QUERY
    mutation {
      removeLabelsFromLabelable(
        input: {
          labelIds: ["#{label_id}"],
          labelableId: "#{node_id}",
          clientMutationId: "rubyGraphQL"
        }
      ) {
        clientMutationId
      }
    }
    QUERY

    GitHub.new.mutate(graphql: query)
  end

  def close_as_outdated
    query = <<~QUERY
    mutation {
      closeDiscussion(
        input: {
          discussionId: "#{self.id}",
          reason: OUTDATED,
          clientMutationId: "rubyGraphQL"
        }
      ) {
        clientMutationId
      }
    }
    QUERY

    GitHub.new.mutate(graphql: query)
  end

  def self.should_comment?(discussion_number: nil, owner: nil, repo: nil)
    return false if owner.nil? || repo.nil?
    return false if discussion_number.nil?

    query = <<~QUERY
    {
      repository(owner: "#{owner}", name: "#{repo}") {
        discussion(number: #{discussion_number}) {
          labels(first:100) {
            nodes {
              name
            }
          }
          comments(first:100) {
            nodes {
              author {
                login
              }
            }
          }
        }
      }
    }
    QUERY

    response = GitHub.new.post(graphql: query)
      .map { |r|
        {
          labels: r.dig("discussion", "labels", "nodes").map { |l|  l["name"] },
          comments_by: r.dig("discussion", "comments", "nodes").map { |c| c.dig("author", "login") }
        }
      }.first

    return false unless response[:labels].include?("Product Feedback") || response[:labels].include?("Bug")

    return false if response[:comments_by].include?("github-actions")

    true
  end
end
