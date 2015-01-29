#!/usr/bin/env ruby

require 'mechanize'

agent = Mechanize.new
agent.user_agent_alias = 'Mac Safari'

`mkdir -p brds/tmp`
`mkdir brds/keep`

page = agent.get('https://github.com/search?utf8=%E2%9C%93&q=layer+extension%3Abrd')
100.times do |i|
    page.links_with(:href => /\.brd$/).each do |link|
        url = 'https://raw.githubusercontent.com' + link.href.gsub("blob/","")
        puts url.chars.last(30).join
        `wget -q -nc --random-wait -P brds/tmp "#{url}"`
        name = `ls brds/tmp/`.strip
        n=`countparts.py "brds/tmp/#{name}"`.to_i
        print n
        if n >= 15
            puts " -- keeper"
            `cp brds/tmp/* brds/keep/`
        else
            puts " -- too easy"
        end
        `rm -f brds/tmp/*`
    end
    link = page.link_with(:href => /search/, :class => /next_page/)
    puts link.href
    page = agent.click(link)
end



