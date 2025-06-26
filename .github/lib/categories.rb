# frozen_string_literal: true

Category = Struct.new(
  :id,
  :name,
  :answerable,
  :discussions
) do
  def self.all(owner: nil, repo: nil)
    return [] if owner.nil? || repo.nil?

    query = <<~QUERY
    {
      repository(owner: "#{owner}", name: "#{repo}"){
        discussionCategories(first: 100) {
          nodes {
            id
            name
            isAnswerable
          }
        }
      }
      rateLimit {
        limit
        cost
        remaining
        resetAt
      }
    }
    QUERY

    GitHub.new.post(graphql: query).first.dig("discussionCategories", "nodes")
      .map do |c|
        Category.new(
          c["id"],
          c["name"],
          c["isAnswerable"]
        )
      end
  end
end
