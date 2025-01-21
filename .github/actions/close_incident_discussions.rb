#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative "../lib/github"
require_relative "../lib/discussions"
require "active_support"
require "active_support/core_ext/date_and_time/calculations"
require "active_support/core_ext/numeric/time"
require "date"

# this action checks for any open incident discussions older than 2 days, and then closes them

discussions = Discussion.find_open_incident_discussions(owner: "community", repo: "community").keep_if { |d| DateTime.parse(d.created_at) < 2.days.ago }

if discussions.length == 0
  puts "No applicable discussions found, exiting"
  exit
end

discussions.each do |d|
  # if a public summary has not been provided, find the most recent incident comment and mark it as the answer
  unless d.is_answered
    comment_id = d.find_most_recent_incident_comment_id(actor_login: "github-actions")

    unless comment_id.nil?
      Discussion.mark_comment_as_answer(comment_id:)
    end

    # an incident that has been declared as "resolved" should have already updated the post body, this is in case that step failed.
    unless d.body.include?("https://github.com/community/community/blob/main/.github/src/incident_resolved.png?raw=true")
      updated_body = "![A dark background with two security-themed abstract shapes positioned in the top left and bottom right corners. In the center of the image, bold white text reads \\\"Incident Resolved\\\" with a white Octocat logo.](https://github.com/community/community/blob/main/.github/src/incident_resolved.png?raw=true) \n #{d.body}"
      d.update_discussion(body: updated_body)
    end
  end

  d.close_as_resolved
end
