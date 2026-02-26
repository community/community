#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative "../lib/github"
require_relative "../lib/discussions"

# This script takes the public incident summary, adds it as a comment to the incident, and then marks that comment as the answer.

# first, we must identify the correct incident to update, in the case where there are multiple open incident discussions.
selected_discussion = Discussion.find_open_incident_discussions(owner: "community", repo: "community").keep_if { |d| d.body.include?("#{ENV["INCIDENT_SLUG"]}") }.first

if selected_discussion.nil?
  puts "No applicable discussion, exiting"
  exit
end

# add the summary as a comment to the discussion
summary = "### Incident Summary \n #{ENV["INCIDENT_PUBLIC_SUMMARY"]}"
comment_id = selected_discussion.add_comment(body: summary).dig("data", "addDiscussionComment", "comment", "id")

# mark this new comment as the answer
# (note that we don't need the discussion's context for this, so we don't call it on the instance of Discussion but on the struct)
Discussion.mark_comment_as_answer(comment_id:)

# update the post body to include the resolved picture, but only if the post body has not already been updated.
unless selected_discussion.body.include?("https://github.com/community/community/blob/main/.github/src/incident_resolved.png?raw=true")
  updated_body = "![A dark background with two security-themed abstract shapes positioned in the top left and bottom right corners. In the center of the image, bold white text reads \\\"Incident Resolved\\\" with a white Octocat logo.](https://github.com/community/community/blob/main/.github/src/incident_resolved.png?raw=true) \n \n #{selected_discussion.body}"
  selected_discussion.update_discussion(body: updated_body)
end
