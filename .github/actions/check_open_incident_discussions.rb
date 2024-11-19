#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative "../lib/github"
require_relative "../lib/discussion"
require "active_support"
require "active_support/core_ext/date_and_time/calculations"
require "active_support/core_ext/numeric/time"

# this action checks for any open incident discussions older than 2 days, returns an array of discussion IDs

discussions = Discussion.find_open_incident_discussions(owner: "community", repo: "community")

discussions.keep_if { |d| Time.parse(d["createdAt"]) < 2.days.ago }.map! { |d| d["id"] }

`echo "DISCUSSION_IDS"=#{discussions} >> $GITHUB_OUTPUT`
