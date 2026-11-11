#include <sys/json.h>
#include <algorithm>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <vector>

struct Group {
    std::set<std::string> addresses;
    std::map<int,std::set<std::string>> scans;
    unsigned observations=0;
};
static std::string getstr(json_decoder_t* d,const char* key) {
    const char* p=nullptr;
    return json_decoder_get_string(d,key,&p,true)==JSON_DECODER_OK && p?p:"";
}
static int getint(json_decoder_t* d,const char* key) {
    int n=0;json_decoder_get_int(d,key,&n,true);return n;
}
int main(int argc,char** argv) {
    if(argc>2){std::cerr<<"Usage: toretto-qnx-live [max-groups]\\n";return 2;}
    unsigned max_groups=2048;
    constexpr size_t max_scans_per_group=64;
    constexpr size_t max_addresses_per_group=32;
    if(argc==2){try {max_groups=static_cast<unsigned>(std::stoul(argv[1]));}catch(...){return 2;}if(max_groups==0||max_groups>65536)return 2;}
    std::map<std::string,Group> groups;
    std::string line;
    unsigned long long windows=0,total=0;
    constexpr size_t max_line_bytes=4*1024*1024;
    // Bound memory even when the input contains no newline. Discard the
    // remainder of an oversized record before processing the next one.
    while(true) {
        line.clear();
        bool oversized=false;
        bool saw_any=false;
        for(;;) {
            const int ch=std::cin.get();
            if(ch==std::char_traits<char>::eof())break;
            saw_any=true;
            if(ch==10)break;
            if(line.size()<max_line_bytes)line.push_back(static_cast<char>(ch));
            else oversized=true;
        }
        if(!saw_any && line.empty())break;
        if(oversized){std::cerr<<"oversized line\\n";continue;}
        json_decoder_t* d=json_decoder_create();if(!d)return 2;
        bool ok=json_decoder_parse_json_str(d,line.c_str())==JSON_DECODER_OK && json_decoder_push_object(d,nullptr,false)==JSON_DECODER_OK;
        if(!ok){std::cerr<<"invalid event\\n";json_decoder_destroy(d);continue;}
        if(getstr(d,"event")!="ble_window"){json_decoder_destroy(d);continue;}
        if(json_decoder_push_array(d,"identity_observations",false)!=JSON_DECODER_OK){json_decoder_destroy(d);continue;}
        const int count=json_decoder_length(d);
        unsigned accepted=0;
        for(int i=0;i<count;i++) {
            if(json_decoder_push_object(d,nullptr,false)!=JSON_DECODER_OK)break;
            const auto fp=getstr(d,"fingerprint"),addr=getstr(d,"address");const int scan=getint(d,"scan_id");
            if(!fp.empty()&&!addr.empty()) {
                auto it=groups.find(fp);
                if(it!=groups.end()||groups.size()<max_groups) {
                    auto& g=groups[fp];
                    if(g.addresses.size()<max_addresses_per_group || g.addresses.count(addr))g.addresses.insert(addr);
                    if(g.scans.size()<max_scans_per_group || g.scans.count(scan)) {
                        auto& addresses=g.scans[scan];
                        if(addresses.size()<max_addresses_per_group || addresses.count(addr))addresses.insert(addr);
                    }
                    ++g.observations;++accepted;++total;
                }
            }
            json_decoder_pop(d);
        }
        json_decoder_destroy(d);
        ++windows;
        unsigned shared=0,handed=0,multiple=0;
        for(const auto& [fp,g]:groups) {
            if(g.addresses.size()>1)++shared;
            unsigned handoffs=0;std::string last;bool have=false;bool multi=false;
            for(const auto& [scan,addrs]:g.scans){(void)scan;if(addrs.empty())continue;if(addrs.size()>1){multi=true;continue;}const auto& a=*addrs.begin();if(have&&last!=a)++handoffs;last=a;have=true;}
            if(handoffs>=3)++handed;
            if(multi)++multiple;
        }
        std::cout<<"{\"engine\":\"toretto-qnx-live\",\"windows\":"<<windows<<",\"accepted_in_window\":"<<accepted<<",\"total_observations\":"<<total<<",\"fingerprint_groups\":"<<groups.size()<<",\"shared_payload_groups\":"<<shared<<",\"repeated_handoff_groups\":"<<handed<<",\"multi_address_window_groups\":"<<multiple<<"}"<<std::endl;
    }
}
