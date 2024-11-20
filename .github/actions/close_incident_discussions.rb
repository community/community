#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative "../lib/github"
require_relative "../lib/discussion"
require "active_support"
require "active_support/core_ext/date_and_time/calculations"
require "active_support/core_ext/numeric/time"

# this action checks for any open incident discussions older than 2 days, and then closes them

discussions = Discussion.find_open_incident_discussions(owner: "community", repo: "community")

discussion_ids = discussions.keep_if { |d| Time.parse(d["createdAt"]) < 2.days.ago }.map! { |d| d["id"] }

if discussion_ids.length == 0
  puts "No discussion IDs provided, exiting"
  exit
end

discussion_ids.each do |d_id|
  # if a public summary has not been provided, find the most recent incident comment and mark it as the answer
  unless Discussion.is_answered?(id: d_id)
    comment_id = Discussion.find_most_recent_incident_comment_id(id: d_id, actor_login: "github-actions")

    unless comment_id.nil?
      Discussion.mark_comment_as_answer(comment_id:)
    end

    updated_body = "![A dark background with two security-themed abstract shapes positioned in the top left and bottom right corners. In the center of the image, bold white text reads \\\"Incident Resolved\\\" with a white Octocat logo.](https://github.com/community/incident-discussion-bot/blob/main/.github/src/incident_resolved.png?raw=true) \n #{Discussion.find_by_id(id: d_id)["body"]}"
    Discussion.update_discussion(id: d_id, body: updated_body)
  end

  Discussion.close_as_resolved(id: d_id)
end
