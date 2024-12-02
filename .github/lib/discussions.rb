# frozen_string_literal: true

require "active_support"
require "active_support/core_ext/date_and_time/calculations"
require "active_support/core_ext/numeric/time"

Discussion = Struct.new(
  :id,
  :url,
  :title,
  :labelled,
  :body,
  :created_at,
  :is_answered
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
          body: """#{body}""",
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

      p response
    return false unless response[:labels].include?("Product Feedback") || response[:labels].include?("Bug")

    return false if response[:comments_by].include?("github-actions")

    true
  end

  def self.create_incident_discussion(repo_id:, title:, body:, category_id:, labels:)
    # create a new discussion in the specified category, applies the incident label, and returns the discussion id
    return if repo_id.nil? || title.nil? || body.nil? || category_id.nil?

    query = <<~QUERY
    mutation {
      createDiscussion(
        input: {
          categoryId: "#{category_id}",
          repositoryId: "#{repo_id}",
          clientMutationId: "rubyGraphQL",
          title: "#{title}",
          body: "#{body}"
        }
      ) {
      clientMutationId
      discussion {
        id
        body
        }
      }
    }
    QUERY

    incident_discussion_id = GitHub.new.mutate(graphql: query).dig("data", "createDiscussion", "discussion", "id")

    if labels
      addLabel = <<~QUERY
      mutation {
       addLabelsToLabelable(
          input: {
            labelIds: #{labels},
            labelableId: "#{incident_discussion_id}",
            clientMutationId: "rubyGraphQL"
          }
        ) {
          clientMutationId

        }
      }
      QUERY

      GitHub.new.mutate(graphql: addLabel)
    end
  end

  def self.mark_comment_as_answer(comment_id:)
    # marks the given comment as the answer
    return if comment_id.nil?

    query = <<~QUERY
    mutation {
      markDiscussionCommentAsAnswer(
        input: {
          id: "#{comment_id}",
          clientMutationId: "rubyGraphQL"
        }
      ) {
        clientMutationId
        discussion {
          id
          answer {
            id
          }
        }
      }
    }
    QUERY

    GitHub.new.mutate(graphql: query)
  end

  def update_discussion(body:)
    return if body.nil?

    query = <<~QUERY
    mutation {
      updateDiscussion(
        input: {
          discussionId: "#{self.id}",
          body: "#{body}",
          clientMutationId: "rubyGraphQL"
        }
      ) {
        clientMutationId
        discussion {
          id
        }
      }
    }
    QUERY

    GitHub.new.mutate(graphql: query)
  end

  def find_most_recent_incident_comment_id(actor_login:)
    # finds the most recent comment generated by an incident action
    return nil if actor_login.nil?

    query = <<~QUERY
    query {
      node(id: "#{self.id}") {
        ... on Discussion {
          id
          comments(last: 10) {
            nodes{
              id
              createdAt
              author {
                login
              }
            }
          }
        }
      }
    }
    QUERY

    # with the results, get an array of comments from the given actor login sorted by most recent
    comments = GitHub.new.post(graphql: query).first.dig("comments", "nodes")

    return nil if comments.empty?

    filtered_comments = comments.keep_if { |comment| comment["author"]["login"] == actor_login }
                        &.sort_by { |comment| comment["createdAt"] }
                        .reverse

    # return the most recent comment's ID
    return nil if filtered_comments.empty?
    filtered_comments.first["id"]
  end

  def self.find_open_incident_discussions(owner:, repo:)
    return [] if owner.nil? || repo.nil?

    searchquery = "repo:#{owner}/#{repo} is:open author:github-actions[bot] label:\\\"Incident \:exclamation\:\\\""

    query = <<~QUERY
    {
      search(
        first: 100
        query: "#{searchquery}"
        type: DISCUSSION
      ) {
        discussionCount
        ...Results
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
          body
          createdAt
          isAnswered
        }
      }
    }
    QUERY

    GitHub.new.post(graphql: query)
      .map! { |r| r.dig('nodes') }
      .flatten
      .map do |d|
        Discussion.new(
          d["id"],
          d["url"],
          d["title"],
          false, # :labelled
          d["body"],
          d["createdAt"],
          d["isAnswered"]
        )
      end
  end

  def close_as_resolved
    # closes the post as resolved

    query = <<~QUERY
    mutation {
      closeDiscussion(
        input: {
          discussionId: "#{self.id}",
          reason: RESOLVED,
          clientMutationId: "rubyGraphQL"
        }
      ) {
        clientMutationId
        discussion {
          id
        }
      }
    }
    QUERY

    GitHub.new.mutate(graphql: query)
  end
end
