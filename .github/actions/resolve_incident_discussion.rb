#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative "../lib/github"
require_relative "../lib/discussions"

# This script acts when we receieve an incident resolved dispatch event to update the incident discussion.

# first, we must identify the correct incident to update, in the case where there are multiple open incident discussions.
discussion = Discussion.find_open_incident_discussions(owner: "community", repo: "community").keep_if { |d| d.body.include?("#{ENV["INCIDENT_SLUG"]}") }.first

if discussion.nil?
  puts "No applicable discussion, exiting"
  exit
end

discussion.add_comment(body: "### Incident Resolved \n This incident has been resolved.")
# update the post body to include the resolved picture
updated_body = "![A dark background with two security-themed abstract shapes positioned in the top left and bottom right corners. In the center of the image, bold white text reads \\\"Incident Resolved\\\" with a white Octocat logo.](https://github.com/community/community/blob/main/.github/src/incident_resolved.png?raw=true) \n \n #{discussion.body}"
discussion.update_discussion(body: updated_body)
