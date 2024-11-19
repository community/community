#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative "../lib/github"
require_relative "../lib/discussion"

# This script takes the public incident summary, adds it as a comment to the incident, and then marks that comment as the answer.

# first, we must identify the correct incident to update, in the case where there are multiple open incident discussions.
open_discussions = Discussion.find_open_incident_discussions(owner: "community", repo: "community")
selected_incident = open_discussions.keep_if { |d| d["body"].include?("#{ENV["INCIDENT_SLUG"]}") }.first

# add the summary as a comment to the discussion
summary = "### Incident Summary \n #{ENV["INCIDENT_PUBLIC_SUMMARY"]}"
comment_id = Discussion.add_comment_with_id(id: selected_incident["id"], body: summary)

# mark this new comment as the answer
Discussion.mark_comment_as_answer(comment_id:)

# update the post body to include the resolved picture
updated_body = "![A dark background with two security-themed abstract shapes positioned in the top left and bottom right corners. In the center of the image, bold white text reads \"Incident Resolved\" with a white Octocat logo.](https://github.com/community/incident-discussion-bot/blob/main/.github/src/incident_resolved.png?raw=true) \n \n #{selected_incident["body"]}"
Discussion.update_discussion(id: selected_incident["id"], body: updated_body)
