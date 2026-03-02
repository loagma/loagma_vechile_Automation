pincode conflicts - day 26 analysis notes

ran the script today and got 6 pincodes showing up in multiple areas. spent some time figuring out whats going on

so basically the issue is that pincodes in hyderabad are HUGE. like 500008 covers golconda, gudimalkapur, tolichowki, even parts near manikonda. thats like 5-6 km spread. that's why it's showing up everywhere

also some pincodes are right on the border between zones. 500030 is mostly attapur but one order went to narsingi (kismatpur side probably). makes sense when you think about it

the delivery guys also didnt follow strict pincode rules. they just looked at which vehicle had space, what route made sense, traffic etc. like order 244580 with pincode 500030 went to narsingi even though most 500030 orders went to attapur. probably made sense for that route


the 6 problem pincodes:

500006 - 3 orders
  2 went to asif nagar (mehdipatnam/topekhana)
  1 went to gudimalkapur (attapur road)
  gave it to asif nagar. its a border pincode anyway

500008 - 23 orders (big problem)
  9 golconda
  7 hakimpet
  5 manikonda
  2 gudimalkapur
  assigned to golconda since it has the most
  this pincode is massive, covers golconda fort, tolichowki, shaikpet, manikonda
  9 out of 23 isnt great but best we can do
  areas are close enough so routing should work

500028 - 7 orders
  5 asif nagar (rk pet, rethibowli)
  1 gudimalkapur
  1 yousufguda (masab tank)
  asif nagar wins
  another big pincode

500030 - 6 orders
  5 attapur (dairyform, upperpally)
  1 narsingi (kismatpur)
  obvious choice is attapur
  that narsingi order is on the border

500045 - 3 orders
  2 borabanda
  1 yousufguda
  jawahar nagar area sits between both
  went with borabanda

500089 - 11 orders
  6 narsingi (manchirevula)
  3 manikonda
  2 golconda (puppalaguda)
  narsingi it is
  puppalaguda area is kinda in between everything


so does this work? i think yeah. were using the area where most orders went which means the delivery guys thought it belonged there. 109 out of 120 orders have clean mappings (91%). only 6 pincodes out of 35 are problematic (17%).

even the conflicted ones were picking the dominant area which should work for routing. 500008 is not ideal (only 39% golconda) but those areas are geographically close so algorithm should cluster them ok

issues:
  big pincodes like 500008 will have some misclassified orders
  border orders might be in wrong area
  but still way better than database area_name which is dummy value (AMt for everything)

just gonna go with this. good enough for v1. can refine later with coordinates or sub-zones or proper boundaries but thats lot of work

gets us from useless area names to actual geographic clustering which is what we need


todo:
  done - generated mapping
  pending - update order_fetcher.py 
  pending - test on day 26
  pending - check if trip names make sense
  pending - compare with human allocations

spent like 2 hours on this. 500008 is annoying but cant fix without coordinates. good enough
