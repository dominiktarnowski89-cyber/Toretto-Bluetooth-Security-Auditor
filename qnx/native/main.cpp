#include <sys/json.h>
#include <algorithm>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <vector>

struct Observation { std::string fingerprint, address, observed_at; int scan_id=0; };
static std::string str(json_decoder_t* d,const char* key) { const char* p=nullptr; return json_decoder_get_string(d,key,&p,true)==JSON_DECODER_OK && p ? p : ""; }
static int number(json_decoder_t* d,const char* key) { int n=0; json_decoder_get_int(d,key,&n,true); return n; }
static std::string escape(const std::string& s) { std::string out; for(char c:s){ if(c=='"'||c=='\\'){out+='\\';out+=c;}else if(c=='\n')out+="\\n";else if(static_cast<unsigned char>(c)<32)out+=' ';else out+=c;}return out; }
int main(int argc,char** argv) {
 if(argc!=3){std::cerr<<"Usage: toretto-qnx-analyze input.json output.json\n";return 2;}
 std::ifstream in(argv[1],std::ios::binary); if(!in){std::cerr<<"Cannot read input\n";return 2;}
 std::string data((std::istreambuf_iterator<char>(in)),{}); if(data.size()>32*1024*1024){std::cerr<<"Input exceeds 32 MiB\n";return 2;}
 json_decoder_t* d=json_decoder_create();if(!d){return 2;}
 if(json_decoder_parse_json_str(d,data.c_str())!=JSON_DECODER_OK){std::cerr<<"Invalid JSON\n";json_decoder_destroy(d);return 2;}
 if(json_decoder_push_array(d,"identity_observations",false)!=JSON_DECODER_OK){std::cerr<<"Missing identity_observations array\n";json_decoder_destroy(d);return 2;}
 int count=json_decoder_length(d);std::vector<Observation> observations;
 for(int i=0;i<count;i++) {
  if(json_decoder_push_object(d,nullptr,false)!=JSON_DECODER_OK){std::cerr<<"Invalid observation\n";json_decoder_destroy(d);return 2;}
  Observation o; o.fingerprint=str(d,"fingerprint");o.address=str(d,"address");o.observed_at=str(d,"observed_at");o.scan_id=number(d,"scan_id");
  if(!o.fingerprint.empty())observations.push_back(o);
  json_decoder_pop(d);
 }
 json_decoder_destroy(d);
 std::map<std::string,std::vector<Observation>> groups;
 for(const auto& o:observations)groups[o.fingerprint].push_back(o);
 std::ofstream out(argv[2]);if(!out){std::cerr<<"Cannot write output\n";return 2;}
 out<<"{\"schema_version\":1,\"engine\":\"toretto-qnx-native\",\"observation_count\":"<<count<<",\"devices\":[";
 bool first=true;
 for(auto& [fp,items]:groups){
  std::sort(items.begin(),items.end(),[](const auto&a,const auto&b){return a.scan_id==b.scan_id?a.observed_at<b.observed_at:a.scan_id<b.scan_id;});
  std::set<std::string> addresses;std::map<int,std::set<std::string>> byscan;
  for(const auto&o:items){addresses.insert(o.address);byscan[o.scan_id].insert(o.address);}
  int handoffs=0,multi=0;std::string last;bool have=false;
  for(const auto&[scan,addrs]:byscan){if(addrs.size()>1){multi++;continue;}const auto& addr=*addrs.begin();if(have&&last!=addr)handoffs++;last=addr;have=true;}
  if(!first)out<<",";first=false;
  out<<"{\"fingerprint\":\""<<escape(fp)<<"\",\"observations\":"<<items.size()<<",\"addresses\":[";
  bool af=true;for(const auto&a:addresses){if(!af)out<<",";af=false;out<<"\""<<escape(a)<<"\"";}
  out<<"],\"address_count\":"<<addresses.size()<<",\"handoffs\":"<<handoffs<<",\"multi_address_scan_windows\":"<<multi<<",\"alerts\":[";
  bool alert=false;auto add=[&](const char* name){if(alert)out<<",";alert=true;out<<"\""<<name<<"\"";};
  if(addresses.size()>1)add("shared_payload_multiple_addresses");
  if(handoffs>=3)add("repeated_address_handoff");
  if(multi>0)add("multiple_addresses_within_scan_window");
  out<<"]}";
 }
 out<<"],\"evidence_note\":\"Shared BLE payload fingerprints do not prove a single physical device or compromise; scan windows do not prove simultaneous transmission.\"}\n";
 std::cout<<"Observations: "<<count<<"; fingerprint groups: "<<groups.size()<<"\n";
}
