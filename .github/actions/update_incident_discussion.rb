#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative "../lib/github"
require_relative "../lib/discussion"

# This script takes the context from the latest update dispatch event and updates the active incident discussion

# first, we must identify the correct incident to update, in the case where there are multiple open incident discussions.
open_discussions = Discussion.find_open_incident_discussions(owner: "community", repo: "community")
selected_incident = open_discussions.keep_if { |d| d["body"].include?("#{ENV["INCIDENT_SLUG"]}") }.first["id"]

# next, we need to update the discussion with the new information
body = "### Update \n #{ENV["INCIDENT_MESSAGE"]}"

Discussion.add_comment_with_id(id: selected_incident, body:)
